import time
from pathlib import Path
from threading import Thread
from queue import PriorityQueue
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
    URL = "https://notifications.delta.chat/notify"
    CONNECTION_TIMEOUT = 60.0       # seconds until http-request is given up
    NOTIFICATION_RETRY_DELAY = 8.0  # seconds with exponential backoff
    MAX_NUMBER_OF_TRIES = 6
    # exponential backoff means we try for 8^5 seconds, approximately 10 hours

    def __init__(self, vmail_dir):
        self.vmail_dir = vmail_dir
        self.notification_dir = vmail_dir / "pending_notifications"
        if not self.notification_dir.exists():
            self.notification_dir.mkdir()
        self.retry_queues = [PriorityQueue() for _ in range(self.MAX_NUMBER_OF_TRIES)]

    def get_metadata_dict(self, addr):
        return FileDict(self.vmail_dir / addr / "metadata.json")

    def add_token_to_addr(self, addr, token):
        with self.get_metadata_dict(addr).modify() as data:
            tokens = data.get(METADATA_TOKEN_KEY)
            if tokens is None:
                data[METADATA_TOKEN_KEY] = [token]
            elif token not in tokens:
                tokens.append(token)

    def remove_token_from_addr(self, addr, token):
        with self.get_metadata_dict(addr).modify() as data:
            tokens = data.get(METADATA_TOKEN_KEY, [])
            if token in tokens:
                tokens.remove(token)

    def get_tokens_for_addr(self, addr):
        return self.get_metadata_dict(addr).read().get(METADATA_TOKEN_KEY, [])

    def new_message_for_addr(self, addr):
        for token in self.get_tokens_for_addr(addr):
            self.notification_dir.joinpath(token).write_text(addr)
            self.add_token_for_retry(token)

    def add_token_for_retry(self, token, retry_num=0):
        if retry_num >= self.MAX_NUMBER_OF_TRIES:
            return False

        when = time.time()
        if retry_num > 0:
            # backup exponentially with number of retries
            when += pow(self.NOTIFICATION_RETRY_DELAY, retry_num)
        self.retry_queues[retry_num].put((when, token))
        return True

    def requeue_persistent_pending_tokens(self):
        for token_path in self.notification_dir.iterdir():
            self.add_token_for_retry(token_path.name)

    def start_notification_threads(self):
        self.requeue_persistent_pending_tokens()
        threads = {}
        for retry_num in range(len(self.retry_queues)):
            num_threads = {0: 4}.get(retry_num, 2)
            threads[retry_num] = []
            for _ in range(num_threads):
                threads[retry_num].append(NotifyThread(self, retry_num))
                threads[retry_num][-1].start()
        return threads


class NotifyThread(Thread):
    def __init__(self, notifier, retry_num):
        super().__init__(daemon=True)
        self.notifier = notifier
        self.retry_num = retry_num

    def stop(self):
        self.notifier.retry_queues[self.retry_num].put((None, None))

    def run(self):
        requests_session = requests.Session()
        while self.retry_one(requests_session):
            pass

    def retry_one(self, requests_session, sleep=time.sleep):
        # takes the next token from the per-retry-number PriorityQueue
        # which is ordered by "when" (as set by add_token_for_retry()).
        # If the request to notification server fails the token is
        # queued to the next retry-number's PriorityQueue
        # until it finally is dropped if MAX_NUMBER_OF_TRIES is exceeded
        when, token = self.notifier.retry_queues[self.retry_num].get()
        if when is None:
            return False
        wait_time = when - time.time()
        if wait_time > 0:
            sleep(wait_time)
        self.perform_request_to_notification_server(requests_session, token)
        return True

    def perform_request_to_notification_server(self, requests_session, token):
        token_path = self.notifier.notification_dir.joinpath(token)
        try:
            timeout = self.notifier.CONNECTION_TIMEOUT
            res = requests_session.post(self.notifier.URL, data=token, timeout=timeout)
        except requests.exceptions.RequestException as e:
            res = e
        else:
            if res.status_code in (200, 410):
                if res.status_code == 410:
                    # 410 Gone: means the token is no longer valid.
                    try:
                        addr = token_path.read_text()
                    except FileNotFoundError:
                        logging.warning("no address for token %r:", token)
                        return
                    self.notifier.remove_token_from_addr(addr, token)
                token_path.unlink(missing_ok=True)
                return

        logging.warning("Notification request failed: %r", res)
        if not self.notifier.add_token_for_retry(token, retry_num=self.retry_num + 1):
            token_path.unlink(missing_ok=True)
            logging.warning("dropping token after %d tries: %r", self.retry_num, token)


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
                res = " ".join(notifier.get_tokens_for_addr(addr))
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
            notifier.add_token_to_addr(addr, value)
        elif keyname[0] == "priv" and keyname[2] == "messagenew":
            notifier.new_message_for_addr(addr)
        else:
            # Transaction failed.
            transactions[transaction_id]["res"] = "F\n"


class ThreadedUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    request_queue_size = 100


def main():
    socket, vmail_dir = sys.argv[1:]

    vmail_dir = Path(vmail_dir)

    if not vmail_dir.exists():
        logging.error("vmail dir does not exist: %r", vmail_dir)
        return 1

    notifier = Notifier(vmail_dir)
    notifier.start_notification_threads()

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

    with ThreadedUnixStreamServer(socket, Handler) as server:
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
