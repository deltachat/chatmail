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


DICTPROXY_LOOKUP_CHAR = "L"
DICTPROXY_SET_CHAR = "S"
DICTPROXY_BEGIN_TRANSACTION_CHAR = "B"
DICTPROXY_COMMIT_TRANSACTION_CHAR = "C"
DICTPROXY_TRANSACTION_CHARS = "SBC"


def handle_dovecot_protocol(rfile, wfile, tokens, requests_session, config: Config):
    # HELLO message, ignored.
    msg = rfile.readline().strip().decode()

    def post_with_token(token):
        response = requests_session.post(
            "https://notifications.delta.chat/notify",
            data=token,
            timeout=60,
        )
        if response.status_code == 410:
            # 410 Gone status code
            # means the token is no longer valid.
            del tokens[guid]

    transactions = {}
    while True:
        msg = rfile.readline().strip().decode()
        if not msg:
            break

        res = handle_dovecot_request(msg, transactions, tokens, post_with_token)
        if res:
            wfile.write(res.encode("ascii"))
            wfile.flush()


def handle_dovecot_request(msg, transactions, tokens, post_with_token):
    # see https://doc.dovecot.org/3.0/developer_manual/design/dict_protocol/
    short_command = msg[0]
    parts = msg[1:].split("\t")
    if short_command == DICTPROXY_LOOKUP_CHAR:
        return b"N\n"

    if short_command not in (DICTPROXY_TRANSACTION_CHARS):
        return

    transaction_id = parts[0]

    if short_command == DICTPROXY_BEGIN_TRANSACTION_CHAR:
        transactions[transaction_id] = b"O\n"
    elif short_command == DICTPROXY_COMMIT_TRANSACTION_CHAR:
        # returns whether it failed or succeeded.
        return transactions.pop(transaction_id, b"N\n")
    elif short_command == DICTPROXY_SET_CHAR:
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

        keyname = parts[1].split("/")
        value = parts[2] if len(parts) > 2 else ""
        if keyname[0] == "priv" and keyname[2] == "devicetoken":
            tokens[keyname[1]] = value
        elif keyname[0] == "priv" and keyname[2] == "messagenew":
            guid = keyname[1]
            token = tokens.get(guid)
            if token:
                post_with_token(token)
        else:
            # Transaction failed.
            transactions[transaction_id] = b"F\n"


class ThreadedUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    request_queue_size = 100


def main():
    socket, username, config = sys.argv[1:]
    passwd_entry = pwd.getpwnam(username)

    # XXX config is not currently used
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
