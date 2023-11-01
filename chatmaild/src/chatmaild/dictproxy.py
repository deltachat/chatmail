import logging
import os
import sys
import json
import crypt
from socketserver import (
    UnixStreamServer,
    StreamRequestHandler,
    ThreadingMixIn,
)
import pwd

from .database import Database

NOCREATE_FILE = "/etc/chatmail-nocreate"


def encrypt_password(password: str):
    # https://doc.dovecot.org/configuration_manual/authentication/password_schemes/
    passhash = crypt.crypt(password, crypt.METHOD_SHA512)
    return "{SHA512-CRYPT}" + passhash


def is_allowed_to_create(user, cleartext_password) -> bool:
    """Return True if user and password are admissable."""
    if os.path.exists(NOCREATE_FILE):
        logging.warning(f"blocked account creation because {NOCREATE_FILE!r} exists.")
        return False

    if len(cleartext_password) < 10:
        logging.warning("Password needs to be at least 10 characters long")
        return False

    parts = user.split("@")
    if len(parts) != 2:
        logging.warning(f"user {user!r} is not a proper e-mail address")
        return False
    localpart, domain = parts

    if domain == "nine.testrun.org":
        # nine.testrun.org policy, username has to be exactly nine chars
        if len(localpart) != 9:
            logging.warning(f"localpart {localpart!r} has not exactly nine chars")
            return False

    return True


def create_user(db, user, encrypted_password):
    with db.write_transaction() as conn:
        conn.create_user(user, encrypted_password)
    return dict(
        home=f"/home/vmail/{user}",
        uid="vmail",
        gid="vmail",
        password=encrypted_password,
    )


def get_user_data(db, user):
    with db.read_connection() as conn:
        result = conn.get_user(user)
    if result:
        result["uid"] = "vmail"
        result["gid"] = "vmail"
    return result


def lookup_userdb(db, user):
    return get_user_data(db, user)


def lookup_passdb(db, user, cleartext_password):
    userdata = get_user_data(db, user)
    if not userdata:
        if not is_allowed_to_create(user, cleartext_password):
            return
        encrypted_password = encrypt_password(cleartext_password)
        userdata = create_user(db=db, user=user, encrypted_password=encrypted_password)
    userdata["password"] = userdata["password"].strip()
    return userdata


def handle_dovecot_request(msg, db, mail_domain):
    print(f"received msg: {msg!r}", file=sys.stderr)
    short_command = msg[0]
    if short_command == "L":  # LOOKUP
        parts = msg[1:].split("\t")
        keyname, user = parts[:2]
        namespace, type, *args = keyname.split("/")
        reply_command = "F"
        res = ""
        if namespace == "shared":
            if type == "userdb":
                if user.endswith(f"@{mail_domain}"):
                    res = lookup_userdb(db, user)
                if res:
                    reply_command = "O"
                else:
                    reply_command = "N"
            elif type == "passdb":
                if user.endswith(f"@{mail_domain}"):
                    res = lookup_passdb(db, user, cleartext_password=args[0])
                if res:
                    reply_command = "O"
                else:
                    reply_command = "N"
        print(f"res: {res!r}", file=sys.stderr)
        json_res = json.dumps(res) if res else ""
        return f"{reply_command}{json_res}\n"
    return None


class ThreadedUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    pass


def main():
    socket = sys.argv[1]
    passwd_entry = pwd.getpwnam(sys.argv[2])
    db = Database(sys.argv[3])
    with open("/etc/mailname", "r") as fp:
        mail_domain = fp.read().strip()

    class Handler(StreamRequestHandler):
        def handle(self):
            while True:
                msg = self.rfile.readline().strip().decode()
                if not msg:
                    break
                res = handle_dovecot_request(msg, db, mail_domain)
                if res:
                    print(f"sending result: {res!r}", file=sys.stderr)
                    self.wfile.write(res.encode("ascii"))
                    self.wfile.flush()

    try:
        os.unlink(socket)
    except FileNotFoundError:
        pass

    with ThreadedUnixStreamServer(socket, Handler) as server:
        os.chown(socket, uid=passwd_entry.pw_uid, gid=passwd_entry.pw_gid)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
