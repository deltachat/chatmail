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


def check_password(password) -> bool:
    """Check password policy"""
    if len(password) < 10:
        return False
    return True


def create_user(db, user, encrypted_password):
    if os.path.exists(NOCREATE_FILE):
        logging.warning(
            f"Didn't create account: {NOCREATE_FILE} exists. Delete the file to enable account creation."
        )
        return
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


def lookup_passdb(db, user, password):
    userdata = get_user_data(db, user)
    if not userdata:
        if not check_password(password):
            logging.warning("Attempt to create an account with a weak password.")
            return
        return create_user(db, user, encrypt_password(password))
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
                    res = lookup_passdb(db, user, password=args[0])
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
