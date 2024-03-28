import pwd

from pathlib import Path
from queue import Queue
from threading import Thread
from socketserver import (
    UnixStreamServer,
    StreamRequestHandler,
    ThreadingMixIn,
)
import sys
import logging
import os
import requests

from .filedict import FileDict


DICTPROXY_HELLO_CHAR = "H"
DICTPROXY_LOOKUP_CHAR = "L"
DICTPROXY_ITERATE_CHAR = "I"
DICTPROXY_BEGIN_TRANSACTION_CHAR = "B"
DICTPROXY_SET_CHAR = "S"
DICTPROXY_COMMIT_TRANSACTION_CHAR = "C"
DICTPROXY_TRANSACTION_CHARS = "BSC"

# each SETMETADATA on this key appends to a list of unique device tokens
# which only ever get removed if the upstream indicates the token is invalid
METADATA_TOKEN_KEY = "devicetoken"


class Notifier:
    def __init__(self, vmail_dir):
        self.vmail_dir = vmail_dir
        self.to_notify_queue = Queue()

    def get_metadata_dict(self, addr):
        addr_path = self.vmail_dir.joinpath(addr)
        return FileDict(addr_path / "metadata.marshalled")

    def add_token(self, addr, token):
        with self.get_metadata_dict(addr).modify() as data:
            tokens = data.get(METADATA_TOKEN_KEY)
            if tokens is None:
                data[METADATA_TOKEN_KEY] = tokens = []
            if token not in tokens:
                tokens.append(token)

    def remove_token(self, addr, token):
        with self.get_metadata_dict(addr).modify() as data:
            tokens = data.get(METADATA_TOKEN_KEY)
            if tokens:
                try:
                    tokens.remove(token)
                except KeyError:
                    pass

    def get_tokens(self, addr):
        return self.get_metadata_dict(addr).read().get(METADATA_TOKEN_KEY, [])

    def new_message_for_addr(self, addr):
        self.to_notify_queue.put(addr)

    def thread_run_loop(self):
        requests_session = requests.Session()
        while 1:
            self.thread_run_one(requests_session)

    def thread_run_one(self, requests_session):
        addr = self.to_notify_queue.get()
        for token in self.get_tokens(addr):
            response = requests_session.post(
                "https://notifications.delta.chat/notify",
                data=token,
                timeout=60,
            )
            if response.status_code == 410:
                # 410 Gone status code
                # means the token is no longer valid.
                self.remove_token(addr, token)


def handle_dovecot_protocol(rfile, wfile, notifier):
    transactions = {}
    while True:
        msg = rfile.readline().strip().decode()
        if not msg:
            break

        res = handle_dovecot_request(msg, transactions, notifier)
        if res:
            wfile.write(res.encode("ascii"))
            wfile.flush()


def handle_dovecot_request(msg, transactions, notifier):
    # see https://doc.dovecot.org/3.0/developer_manual/design/dict_protocol/
    short_command = msg[0]
    parts = msg[1:].split("\t")
    if short_command == DICTPROXY_LOOKUP_CHAR:
        # Lpriv/43f5f508a7ea0366dff30200c15250e3/devicetoken\tlkj123poi@c2.testrun.org
        keyparts = parts[0].split("/")
        if keyparts[0] == "priv":
            keyname = keyparts[2]
            addr = parts[1]
            if keyname == METADATA_TOKEN_KEY:
                res = " ".join(notifier.get_tokens(addr))
                return f"O{res}\n"
        logging.warning("lookup ignored: %r", msg)
        return "N\n"
    elif short_command == DICTPROXY_ITERATE_CHAR:
        # Empty line means ITER_FINISHED.
        # If we don't return empty line Dovecot will timeout.
        return "\n"
    elif short_command == DICTPROXY_HELLO_CHAR:
        return  # no version checking

    if short_command not in (DICTPROXY_TRANSACTION_CHARS):
        logging.warning("unknown dictproxy request: %r", msg)
        return

    transaction_id = parts[0]

    if short_command == DICTPROXY_BEGIN_TRANSACTION_CHAR:
        addr = parts[1]
        transactions[transaction_id] = dict(addr=addr, res="O\n")
    elif short_command == DICTPROXY_COMMIT_TRANSACTION_CHAR:
        # each set devicetoken operation persists directly
        # and does not wait until a "commit" comes
        # because our dovecot config does not involve
        # multiple set-operations in a single commit
        return transactions.pop(transaction_id)["res"]
    elif short_command == DICTPROXY_SET_CHAR:
        # For documentation on key structure see
        # https://github.com/dovecot/core/blob/main/src/lib-storage/mailbox-attribute.h

        keyname = parts[1].split("/")
        value = parts[2] if len(parts) > 2 else ""
        addr = transactions[transaction_id]["addr"]
        if keyname[0] == "priv" and keyname[2] == METADATA_TOKEN_KEY:
            notifier.add_token(addr, value)
        elif keyname[0] == "priv" and keyname[2] == "messagenew":
            notifier.new_message_for_addr(addr)
        else:
            # Transaction failed.
            transactions[transaction_id]["res"] = "F\n"


class ThreadedUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    request_queue_size = 100


def main():
    socket, username, vmail_dir = sys.argv[1:]
    passwd_entry = pwd.getpwnam(username)

    vmail_dir = Path(vmail_dir)

    if not vmail_dir.exists():
        logging.error("vmail dir does not exist: %r", vmail_dir)
        return 1

    notifier = Notifier(vmail_dir)

    class Handler(StreamRequestHandler):
        def handle(self):
            try:
                handle_dovecot_protocol(self.rfile, self.wfile, notifier)
            except Exception:
                logging.exception("Exception in the dovecot dictproxy handler")
                raise

    try:
        os.unlink(socket)
    except FileNotFoundError:
        pass

    # start notifier thread for signalling new messages to
    # Delta Chat notification server

    t = Thread(target=notifier.thread_run_loop)
    t.setDaemon(True)
    t.start()

    with ThreadedUnixStreamServer(socket, Handler) as server:
        os.chown(socket, uid=passwd_entry.pw_uid, gid=passwd_entry.pw_gid)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
