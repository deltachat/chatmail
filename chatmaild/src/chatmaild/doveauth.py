import crypt
import json
import logging
import os
import sys
from pathlib import Path

from .config import Config, read_config
from .database import Database
from .dictproxy import DictProxy

NOCREATE_FILE = "/etc/chatmail-nocreate"


class UnknownCommand(ValueError):
    """dictproxy handler received an unkown command"""


def encrypt_password(password: str):
    # https://doc.dovecot.org/configuration_manual/authentication/password_schemes/
    passhash = crypt.crypt(password, crypt.METHOD_SHA512)
    return "{SHA512-CRYPT}" + passhash


def is_allowed_to_create(config: Config, user, cleartext_password) -> bool:
    """Return True if user and password are admissable."""
    if os.path.exists(NOCREATE_FILE):
        logging.warning(f"blocked account creation because {NOCREATE_FILE!r} exists.")
        return False

    if len(cleartext_password) < config.password_min_length:
        logging.warning(
            "Password needs to be at least %s characters long",
            config.password_min_length,
        )
        return False

    parts = user.split("@")
    if len(parts) != 2:
        logging.warning(f"user {user!r} is not a proper e-mail address")
        return False
    localpart, domain = parts

    if localpart == "echo":
        # echobot account should not be created in the database
        return False

    if (
        len(localpart) > config.username_max_length
        or len(localpart) < config.username_min_length
    ):
        logging.warning(
            "localpart %s has to be between %s and %s chars long",
            localpart,
            config.username_min_length,
            config.username_max_length,
        )
        return False

    return True


def get_user_data(db, config: Config, user, conn=None):
    if user == f"echo@{config.mail_domain}":
        return config.get_user_dict(user)

    if conn is None:
        with db.read_connection() as conn:
            result = conn.get_user(user)
    else:
        result = conn.get_user(user)

    if result:
        result.update(config.get_user_dict(user))
    return result


def lookup_userdb(db, config: Config, user):
    return get_user_data(db, config, user)


def lookup_passdb(db, config: Config, user, cleartext_password):
    if user == f"echo@{config.mail_domain}":
        # Echobot writes password it wants to log in with into /run/echobot/password
        try:
            password = Path("/run/echobot/password").read_text()
        except Exception:
            logging.exception("Exception when trying to read /run/echobot/password")
            return None

        return config.get_user_dict(user, enc_password=encrypt_password(password))

    userdata = get_user_data(db, config, user)
    if userdata:
        return userdata
    if not is_allowed_to_create(config, user, cleartext_password):
        return

    # reading and writing user data needs to be atomic
    # to allow concurrent logins to succeed.
    with db.write_transaction() as conn:
        userdata = get_user_data(db, config, user, conn=conn)
        if userdata:
            return userdata

        enc_password = encrypt_password(cleartext_password)
        q = "INSERT INTO users (addr, password) VALUES (?, ?)"
        conn.execute(q, (user, enc_password))
        print(f"Created address: {user}", file=sys.stderr)
        return config.get_user_dict(user, enc_password=enc_password)


def iter_userdb(db) -> list:
    """Get a list of all user addresses."""
    with db.read_connection() as conn:
        rows = conn.execute("SELECT addr from users").fetchall()
    return [x[0] for x in rows]


def split_and_unescape(s):
    """Split strings using double quote as a separator and backslash as escape character
    into parts."""

    out = ""
    i = 0
    while i < len(s):
        c = s[i]
        if c == "\\":
            # Skip escape character.
            i += 1

            # This will raise IndexError if there is no character
            # after escape character. This is expected
            # as this is an invalid input.
            out += s[i]
        elif c == '"':
            # Separator
            yield out
            out = ""
        else:
            out += c
        i += 1
    yield out


class AuthDictProxy(DictProxy):
    def __init__(self, db, config):
        super().__init__()
        self.db = db
        self.config = config

    def handle_lookup(self, parts):
        # Dovecot <2.3.17 has only one part,
        # do not attempt to read any other parts for compatibility.
        keyname = parts[0]

        namespace, type, args = keyname.split("/", 2)
        args = list(split_and_unescape(args))

        config = self.config
        db = self.db
        reply_command = "F"
        res = ""
        if namespace == "shared":
            if type == "userdb":
                user = args[0]
                if user.endswith(f"@{config.mail_domain}"):
                    res = lookup_userdb(db, config, user)
                if res:
                    reply_command = "O"
                else:
                    reply_command = "N"
            elif type == "passdb":
                user = args[1]
                if user.endswith(f"@{config.mail_domain}"):
                    res = lookup_passdb(db, config, user, cleartext_password=args[0])
                if res:
                    reply_command = "O"
                else:
                    reply_command = "N"
        json_res = json.dumps(res) if res else ""
        return f"{reply_command}{json_res}\n"

    def handle_iterate(self, parts):
        # example: I0\t0\tshared/userdb/
        if parts[2] == "shared/userdb/":
            db = self.db
            result = "".join(f"Oshared/userdb/{user}\t\n" for user in iter_userdb(db))
            return f"{result}\n"


def main():
    socket, cfgpath = sys.argv[1:]
    config = read_config(cfgpath)
    db = Database(config.passdb_path)

    dictproxy = AuthDictProxy(db=db, config=config)

    dictproxy.serve_forever_from_socket(socket)
