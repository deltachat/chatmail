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


class DictProxy:
    def __init__(self, db, mail_domain):
        self.db = db
        self.mail_domain = mail_domain

    def create_user(self, user, password):
        if os.path.exists(NOCREATE_FILE):
            logging.warning(f"Didn't create account: {NOCREATE_FILE} exists.")
            return
        with self.db.write_transaction() as conn:
            conn.create_user(user, password)
        return dict(home=f"/home/vmail/{user}", uid="vmail", gid="vmail", password=password)

    def get_user_data(self, user):
        with self.db.read_connection() as conn:
            result = conn.get_user(user)
        if result:
            result["uid"] = "vmail"
            result["gid"] = "vmail"
        return result


    def lookup_userdb(self, user):
        return self.get_user_data(user)


    def lookup_passdb(self, user, password):
        userdata = self.get_user_data(user)
        if not userdata:
            return self.create_user(user, encrypt_password(password))
        userdata["password"] = userdata["password"].strip()
        return userdata


    def handle_dovecot_request(self, msg):
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
                    if user.endswith(f"@{self.mail_domain}"):
                        res = lookup_userdb(db, user)
                    if res:
                        reply_command = "O"
                    else:
                        reply_command = "N"
                elif type == "passdb":
                    if user.endswith(f"@{self.mail_domain}"):
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
    with open("/etc/mailname", "r") as fp:
        mail_domain = fp.read().strip()

    db = Database(sys.argv[3])
    dictproxy = DictProxy(db, mail_domain)
    class Handler(StreamRequestHandler):
        def handle(self):
            while True:
                msg = self.rfile.readline().strip().decode()
                if not msg:
                    break
                res = dictproxy.handle_dovecot_request(msg)
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
