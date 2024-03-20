import pwd

import pathlib
from queue import Queue
from threading import Thread
from socketserver import (
    UnixStreamServer,
    StreamRequestHandler,
    ThreadingMixIn,
)
from .config import read_config
import sys
import logging
import os
import requests
import marshal


DICTPROXY_LOOKUP_CHAR = "L"
DICTPROXY_ITERATE_CHAR = "I"
DICTPROXY_SET_CHAR = "S"
DICTPROXY_BEGIN_TRANSACTION_CHAR = "B"
DICTPROXY_COMMIT_TRANSACTION_CHAR = "C"
DICTPROXY_TRANSACTION_CHARS = "SBC"


class Notifier:
    def __init__(self, metadata_dir):
        self.metadata_dir = metadata_dir
        self.to_notify_queue = Queue()

    def get_metadata(self, guid):
        guid_path = self.metadata_dir.joinpath(guid)
        if guid_path.exists():
            with guid_path.open("rb") as f:
                return marshal.load(f)
        return {}

    def set_metadata(self, guid, guid_data):
        guid_path = self.metadata_dir.joinpath(guid)
        write_path = guid_path.with_suffix(".tmp")
        with write_path.open("wb") as f:
            marshal.dump(guid_data, f)
        os.rename(write_path, guid_path)

    def set_token(self, guid, token):
        guid_data = self.get_metadata(guid)
        guid_data["token"] = token
        self.set_metadata(guid, guid_data)

    def del_token(self, guid):
        guid_data = self.get_metadata(guid)
        if "token" in guid_data:
            del guid_data["token"]
            self.set_metadata(guid, guid_data)

    def get_token(self, guid):
        return self.get_metadata(guid).get("token")

    def new_message_for_guid(self, guid):
        self.to_notify_queue.put(guid)

    def thread_run_loop(self):
        requests_session = requests.Session()
        while 1:
            self.thread_run_one(requests_session)

    def thread_run_one(self, requests_session):
        guid = self.to_notify_queue.get()
        token = self.get_token(guid)
        if token:
            response = requests_session.post(
                "https://notifications.delta.chat/notify",
                data=token,
                timeout=60,
            )
            if response.status_code == 410:
                # 410 Gone status code
                # means the token is no longer valid.
                self.del_token(guid)


def handle_dovecot_protocol(rfile, wfile, notifier):
    # HELLO message, ignored.
    msg = rfile.readline().strip().decode()

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
        return "N\n"
    elif short_command == DICTPROXY_ITERATE_CHAR:
        # Empty line means ITER_FINISHED.
        # If we don't return empty line Dovecot will timeout.
        return "\n"

    if short_command not in (DICTPROXY_TRANSACTION_CHARS):
        return

    transaction_id = parts[0]

    if short_command == DICTPROXY_BEGIN_TRANSACTION_CHAR:
        transactions[transaction_id] = "O\n"
    elif short_command == DICTPROXY_COMMIT_TRANSACTION_CHAR:
        # returns whether it failed or succeeded.
        return transactions.pop(transaction_id, "N\n")
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
            notifier.set_token(keyname[1], value)
        elif keyname[0] == "priv" and keyname[2] == "messagenew":
            notifier.new_message_for_guid(keyname[1])
        else:
            # Transaction failed.
            transactions[transaction_id] = "F\n"


class ThreadedUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    request_queue_size = 100


def main():
    socket, username, config, metadata_dir = sys.argv[1:]
    passwd_entry = pwd.getpwnam(username)

    # XXX config is not currently used
    config = read_config(config)
    metadata_dir = pathlib.Path(metadata_dir)
    if not metadata_dir.exists():
        metadata_dir.mkdir()
    notifier = Notifier(metadata_dir)

    class Handler(StreamRequestHandler):
        def handle(self):
            try:
                handle_dovecot_protocol(self.rfile, self.wfile, notifier)
            except Exception:
                logging.exception("Exception in the handler")
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
