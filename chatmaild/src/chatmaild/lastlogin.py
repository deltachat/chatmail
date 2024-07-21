import os
import sys
import time

from .config import read_config
from .dictproxy import DictProxy

# this file's mtime reflects the last login-time for a user
LAST_LOGIN = "last-login"


def get_daytimestamp(timestamp) -> int:
    return int(timestamp) // 86400 * 86400


def write_last_login_to_userdir(userdir, timestamp):
    target = userdir.joinpath(LAST_LOGIN)
    timestamp = get_daytimestamp(timestamp)
    try:
        st = target.stat()
    except FileNotFoundError:
        # only happens on initial login
        userdir.mkdir(exist_ok=True)
        target.touch()
        os.utime(target, (timestamp, timestamp))
    else:
        if st.st_mtime < timestamp:
            os.utime(target, (timestamp, timestamp))


def get_last_login_from_userdir(userdir) -> int:
    target = userdir.joinpath(LAST_LOGIN)
    try:
        return int(target.stat().st_mtime)
    except FileNotFoundError:
        # during migration many directories will not have last-login file
        # so we write it here to the current time
        target.touch()
        timestamp = get_daytimestamp(time.time())
        os.utime(target, (timestamp, timestamp))
        return timestamp


class LastLoginDictProxy(DictProxy):
    def __init__(self, config):
        super().__init__()
        self.config = config

    def handle_set(self, transaction_id, parts):
        keyname = parts[1].split("/")
        value = parts[2] if len(parts) > 2 else ""
        addr = self.transactions[transaction_id]["addr"]
        if keyname[0] == "shared" and keyname[1] == "last-login":
            addr = keyname[2]
            timestamp = int(value)
            userdir = self.config.get_user_maildir(addr)
            write_last_login_to_userdir(userdir, timestamp)
        else:
            # Transaction failed.
            self.transactions[transaction_id]["res"] = "F\n"


def main():
    socket, config_path = sys.argv[1:]
    config = read_config(config_path)
    dictproxy = LastLoginDictProxy(config=config)
    dictproxy.serve_forever_from_socket(socket)
