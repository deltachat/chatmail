import os
import sys
import time

import filelock

from .config import read_config
from .dictproxy import DictProxy

# this file's mtime reflects the last login-time for a user
LAST_LOGIN = "password"


def get_daytimestamp(timestamp) -> int:
    return int(timestamp) // 86400 * 86400


def write_last_login_to_userdir(userdir, timestamp):
    target = userdir.joinpath(LAST_LOGIN)
    timestamp = get_daytimestamp(timestamp)
    try:
        s = os.stat(target)
    except FileNotFoundError:
        pass
    else:
        if int(s.st_mtime) != timestamp:
            os.utime(target, (timestamp, timestamp))


def get_last_login_from_userdir(userdir) -> int:
    if "@" not in userdir.name or userdir.name.startswith("echo@"):
        return get_daytimestamp(time.time())
    target = userdir.joinpath(LAST_LOGIN)
    return int(target.stat().st_mtime)


def set_user_password(config, addr, enc_password):
    assert not addr.startswith("echo@"), addr
    userdir = config.get_user_maildir(addr)
    userdir.mkdir(exist_ok=True)
    password_path = userdir.joinpath("password")
    lock_path = password_path.with_suffix(".lock")
    with filelock.FileLock(lock_path):
        password_path.write_bytes(enc_password.encode("ascii"))


class LastLoginDictProxy(DictProxy):
    def __init__(self, config):
        super().__init__()
        self.config = config

    def handle_set(self, transaction_id, parts):
        keyname = parts[1].split("/")
        value = parts[2] if len(parts) > 2 else ""
        addr = self.transactions[transaction_id]["addr"]
        if keyname[0] == "shared" and keyname[1] == "last-login":
            if addr.startswith("echo@"):
                return
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
