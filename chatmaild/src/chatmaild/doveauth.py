import hashlib
import json
import logging
import os
import sys
import time
import passlib.hash
from pathlib import Path
from socketserver import (
    StreamRequestHandler,
    ThreadingMixIn,
    UnixStreamServer,
)

from .config import Config, read_config
from .database import Database

NOCREATE_FILE = "/etc/chatmail-nocreate"


class UnknownCommand(ValueError):
    """dictproxy handler received an unkown command"""


def encrypt_password(password: str):
    # https://doc.dovecot.org/configuration_manual/authentication/password_schemes/
    pw = passlib.hash.sha512_crypt.hash(password).split("$")
    return "{SHA512-CRYPT}$" + pw[1] + "$" + pw[3] + "§" + pw[4]


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

    return True


def get_user_data(db, config: Config, user):
    if user == f"echo@{config.mail_domain}":
        return dict(
            home=f"/home/vmail/mail/{config.mail_domain}/echo@{config.mail_domain}",
            uid="vmail",
            gid="vmail",
        )

    with db.read_connection() as conn:
        result = conn.get_user(user)
    if result:
        result["home"] = f"/home/vmail/mail/{config.mail_domain}/{user}"
        result["uid"] = "vmail"
        result["gid"] = "vmail"
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

        return dict(
            home=f"/home/vmail/mail/{config.mail_domain}/echo@{config.mail_domain}",
            uid="vmail",
            gid="vmail",
            password=encrypt_password(password),
        )

    with db.write_transaction() as conn:
        userdata = conn.get_user(user)
        if userdata:
            # Update last login time.
            conn.execute(
                "UPDATE users SET last_login=? WHERE addr=?", (int(time.time()), user)
            )

            userdata["home"] = f"/home/vmail/mail/{config.mail_domain}/{user}"
            userdata["uid"] = "vmail"
            userdata["gid"] = "vmail"
            return userdata
        if not is_allowed_to_create(config, user, cleartext_password):
            return

        encrypted_password = encrypt_password(cleartext_password)
        q = """INSERT INTO users (addr, password, last_login)
               VALUES (?, ?, ?)"""
        conn.execute(q, (user, encrypted_password, int(time.time())))
        return dict(
            home=f"/home/vmail/mail/{config.mail_domain}/{user}",
            uid="vmail",
            gid="vmail",
            password=encrypted_password,
        )


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


def handle_dovecot_request(msg, db, config: Config):
    # see https://doc.dovecot.org/3.0/developer_manual/design/dict_protocol/
    short_command = msg[0]
    if short_command == "H":  # HELLO
        # we don't do any checking on versions and just return
        return
    elif short_command == "L":  # LOOKUP
        parts = msg[1:].split("\t")

        # Dovecot <2.3.17 has only one part,
        # do not attempt to read any other parts for compatibility.
        keyname = parts[0]

        namespace, type, args = keyname.split("/", 2)
        args = list(split_and_unescape(args))

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
    raise UnknownCommand(msg)


def handle_dovecot_protocol(rfile, wfile, db: Database, config: Config):
    while True:
        msg = rfile.readline().strip().decode()
        if not msg:
            break
        try:
            res = handle_dovecot_request(msg, db, config)
        except UnknownCommand:
            logging.warning("unknown command: %r", msg)
        else:
            if res:
                wfile.write(res.encode("ascii"))
                wfile.flush()


class ThreadedUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    request_queue_size = 100


def main():
    socket = sys.argv[1]
    db = Database(sys.argv[2])
    config = read_config(sys.argv[3])

    class Handler(StreamRequestHandler):
        def handle(self):
            try:
                handle_dovecot_protocol(self.rfile, self.wfile, db, config)
            except Exception:
                logging.exception("Exception in the handler")
                raise

    try:
        os.unlink(socket)
    except FileNotFoundError:
        pass

    with ThreadedUnixStreamServer(socket, Handler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
