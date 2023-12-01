import logging
import os
import time
import sys
import json
from socketserver import (
    UnixStreamServer,
    StreamRequestHandler,
    ThreadingMixIn,
)
import pwd

from .database import Database
from .util import is_allowed_to_create, encrypt_password, get_mail_domain


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
    with db.write_transaction() as conn:
        userdata = conn.get_user(user)
        if userdata:
            # Update last login time.
            conn.execute(
                "UPDATE users SET last_login=? WHERE addr=?", (int(time.time()), user)
            )

            userdata["uid"] = "vmail"
            userdata["gid"] = "vmail"
            return userdata
        if not is_allowed_to_create(user, cleartext_password):
            return

        encrypted_password = encrypt_password(cleartext_password)
        q = """INSERT INTO users (addr, password, last_login)
               VALUES (?, ?, ?)"""
        conn.execute(q, (user, encrypted_password, int(time.time())))
        return dict(
            home=f"/home/vmail/{user}",
            uid="vmail",
            gid="vmail",
            password=encrypted_password,
        )


def handle_dovecot_request(msg, db, mail_domain):
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
        json_res = json.dumps(res) if res else ""
        return f"{reply_command}{json_res}\n"
    return None


class ThreadedUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    request_queue_size = 100


def main():
    socket = sys.argv[1]
    passwd_entry = pwd.getpwnam(sys.argv[2])
    db = Database(sys.argv[3])
    mail_domain = get_mail_domain()

    class Handler(StreamRequestHandler):
        def handle(self):
            try:
                while True:
                    msg = self.rfile.readline().strip().decode()
                    if not msg:
                        break
                    res = handle_dovecot_request(msg, db, mail_domain)
                    if res:
                        self.wfile.write(res.encode("ascii"))
                        self.wfile.flush()
                    else:
                        logging.warn("request had no answer: %r", msg)
            except Exception:
                logging.exception("Exception in the handler")
                raise

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
