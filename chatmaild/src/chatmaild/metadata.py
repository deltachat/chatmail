import logging
import sys

from .config import read_config
from .dictproxy import DictProxy
from .filedict import FileDict
from .notifier import Notifier


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


class MetadataDictProxy(DictProxy):
    def __init__(self, notifier, metadata, iroh_relay=None):
        super().__init__()
        self.notifier = notifier
        self.metadata = metadata
        self.iroh_relay = iroh_relay

    def handle_lookup(self, parts):
        # Lpriv/43f5f508a7ea0366dff30200c15250e3/devicetoken\tlkj123poi@c2.testrun.org
        keyparts = parts[0].split("/", 2)
        if keyparts[0] == "priv":
            keyname = keyparts[2]
            addr = parts[1]
            if keyname == self.metadata.DEVICETOKEN_KEY:
                res = " ".join(self.metadata.get_tokens_for_addr(addr))
                return f"O{res}\n"
        elif keyparts[0] == "shared":
            keyname = keyparts[2]
            if (
                keyname == "vendor/vendor.dovecot/pvt/server/vendor/deltachat/irohrelay"
                and self.iroh_relay
            ):
                # Handle `GETMETADATA "" /shared/vendor/deltachat/irohrelay`
                return f"O{self.iroh_relay}\n"
        logging.warning(f"lookup ignored: {parts!r}")
        return "N\n"

    def handle_set(self, addr, parts):
        # For documentation on key structure see
        # https://github.com/dovecot/core/blob/main/src/lib-storage/mailbox-attribute.h
        keyname = parts[1].split("/")
        value = parts[2] if len(parts) > 2 else ""
        if keyname[0] == "priv" and keyname[2] == self.metadata.DEVICETOKEN_KEY:
            self.metadata.add_token_to_addr(addr, value)
            return True
        elif keyname[0] == "priv" and keyname[2] == "messagenew":
            self.notifier.new_message_for_addr(addr, self.metadata)
            return True

        return False


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

    dictproxy = MetadataDictProxy(
        notifier=notifier, metadata=metadata, iroh_relay=iroh_relay
    )

    dictproxy.serve_forever_from_socket(socket)
