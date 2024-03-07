import pwd
from socketserver import (
    UnixStreamServer,
    StreamRequestHandler,
    ThreadingMixIn,
)
from .config import read_config, Config
import sys
import logging
import os
import requests


def handle_dovecot_protocol(rfile, wfile, tokens, requests_session, config: Config):
    # HELLO message, ignored.
    msg = rfile.readline().strip().decode()

    transactions = {}

    while True:
        msg = rfile.readline().strip().decode()
        if not msg:
            break

        res = handle_dovecot_request(msg, tokens, requests_session, config)
        if res:
            wfile.write(res.encode("ascii"))
            wfile.flush()


def handle_dovecot_request(msg, tokens, requests_session, config: Config):
    short_command = msg[0]
    if short_command == "L":
        return b"N\n"
    elif short_command == "S":
        # See header of
        # <https://github.com/dovecot/core/blob/5e7965632395793d9355eb906b173bf28d2a10ca/src/lib-storage/mailbox-attribute.h>
        # for the documentation on the structure of the key.

        # Request GETMETADATA "INBOX" /private/chatmail
        # results in a query for
        # priv/dd72550f05eadc65542a1200cac67ad7/chatmail
        #
        # Request GETMETADATA "" /private/chatmail
        # results in
        # priv/dd72550f05eadc65542a1200cac67ad7/vendor/vendor.dovecot/pvt/server/chatmail

        parts = msg[1:].split("\t")
        transaction_id = parts[0]
        keyname = parts[1].split("/")
        value = parts[2] if len(parts) > 2 else ""
        if keyname[0] == "priv" and keyname[2] == "devicetoken":
            tokens[keyname[1]] = value
        elif keyname[0] == "priv" and keyname[2] == "messagenew":
            guid = keyname[1]
            token = tokens.get(guid)
            if token:
                response = requests_session.post(
                    "https://notifications.delta.chat/notify",
                    data=token,
                    timeout=60,
                )
                if response.status_code == 410:
                    # 410 Gone status code
                    # means the token is no longer valid.
                    del tokens[guid]
        else:
            # Transaction failed.
            transactions[transaction_id] = b"F\n"
    elif short_command == "B":
        # Begin transaction.
        transaction_id = msg[1:].split("\t")[0]
        transactions[transaction_id] = b"O\n"
    elif short_command == "C":
        # Commit transaction.
        transaction_id = msg[1:].split("\t")[0]
        return transactions.pop(transaction_id, b"N\n")


class ThreadedUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    request_queue_size = 100


def main():
    socket, username, config = sys.argv[1:]
    passwd_entry = pwd.getpwnam(username)
    config = read_config(config)
    tokens = {}
    requests_session = requests.Session()

    class Handler(StreamRequestHandler):
        def handle(self):
            try:
                handle_dovecot_protocol(
                    self.rfile, self.wfile, tokens, requests_session, config
                )
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
