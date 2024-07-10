import logging
import os
import sys
from socketserver import (
    StreamRequestHandler,
    ThreadingMixIn,
    UnixStreamServer,
)

from .config import read_config
from .filedict import FileDict
from .notifier import Notifier

DICTPROXY_HELLO_CHAR = "H"
DICTPROXY_LOOKUP_CHAR = "L"
DICTPROXY_ITERATE_CHAR = "I"
DICTPROXY_BEGIN_TRANSACTION_CHAR = "B"
DICTPROXY_SET_CHAR = "S"
DICTPROXY_COMMIT_TRANSACTION_CHAR = "C"
DICTPROXY_TRANSACTION_CHARS = "BSC"


class Metadata:
    # each SETMETADATA on this key appends to a list of unique device tokens
    # which only ever get removed if the upstream indicates the token is invalid
    DEVICETOKEN_KEY = "devicetoken"

    def __init__(self, vmail_dir):
        self.vmail_dir = vmail_dir

    def get_metadata_dict(self, addr):
        return FileDict(self.vmail_dir / addr / "metadata.json")

    def add_token_to_addr(self, addr, token):
        with self.get_metadata_dict(addr).modify() as data:
            tokens = data.setdefault(self.DEVICETOKEN_KEY, [])
            if token not in tokens:
                tokens.append(token)

    def remove_token_from_addr(self, addr, token):
        with self.get_metadata_dict(addr).modify() as data:
            tokens = data.get(self.DEVICETOKEN_KEY, [])
            if token in tokens:
                tokens.remove(token)

    def get_tokens_for_addr(self, addr):
        mdict = self.get_metadata_dict(addr).read()
        return mdict.get(self.DEVICETOKEN_KEY, [])


def handle_dovecot_protocol(rfile, wfile, notifier, metadata, iroh_relay=None):
    transactions = {}
    while True:
        msg = rfile.readline().strip().decode()
        if not msg:
            break

        res = handle_dovecot_request(msg, transactions, notifier, metadata, iroh_relay)
        if res:
            wfile.write(res.encode("ascii"))
            wfile.flush()


def handle_dovecot_request(msg, transactions, notifier, metadata, iroh_relay=None):
    # see https://doc.dovecot.org/3.0/developer_manual/design/dict_protocol/
    short_command = msg[0]
    parts = msg[1:].split("\t")
    if short_command == DICTPROXY_LOOKUP_CHAR:
        # Lpriv/43f5f508a7ea0366dff30200c15250e3/devicetoken\tlkj123poi@c2.testrun.org
        keyparts = parts[0].split("/", 2)
        if keyparts[0] == "priv":
            keyname = keyparts[2]
            addr = parts[1]
            if keyname == metadata.DEVICETOKEN_KEY:
                res = " ".join(metadata.get_tokens_for_addr(addr))
                return f"O{res}\n"
        elif keyparts[0] == "shared":
            keyname = keyparts[2]
            if (
                keyname == "vendor/vendor.dovecot/pvt/server/vendor/deltachat/irohrelay"
                and iroh_relay
            ):
                # Handle `GETMETADATA "" /shared/vendor/deltachat/irohrelay`
                return f"O{iroh_relay}\n"
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
        if keyname[0] == "priv" and keyname[2] == metadata.DEVICETOKEN_KEY:
            metadata.add_token_to_addr(addr, value)
        elif keyname[0] == "priv" and keyname[2] == "messagenew":
            notifier.new_message_for_addr(addr, metadata)
        else:
            # Transaction failed.
            transactions[transaction_id]["res"] = "F\n"


class ThreadedUnixStreamServer(ThreadingMixIn, UnixStreamServer):
    request_queue_size = 100


def main():
    socket, config_path = sys.argv[1:]

    config = read_config(config_path)
    iroh_relay = config.iroh_relay

    vmail_dir = config.mailboxes_dir
    if not vmail_dir.exists():
        logging.error("vmail dir does not exist: %r", vmail_dir)
        return 1

    queue_dir = vmail_dir / "pending_notifications"
    queue_dir.mkdir(exist_ok=True)
    metadata = Metadata(vmail_dir)
    notifier = Notifier(queue_dir)
    notifier.start_notification_threads(metadata.remove_token_from_addr)

    class Handler(StreamRequestHandler):
        def handle(self):
            try:
                handle_dovecot_protocol(
                    self.rfile, self.wfile, notifier, metadata, iroh_relay
                )
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
