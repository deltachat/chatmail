"""
Remove inactive users
"""

import os
import shutil
import sys
import time

from .config import read_config


def delete_inactive_users(config):
    cutoff_date = time.time() - config.delete_inactive_users_after * 86400
    for addr in os.listdir(config.mailboxes_dir):
        try:
            user = config.get_user(addr)
        except ValueError:
            continue

        read_timestamp = user.get_last_login_timestamp()
        if read_timestamp and read_timestamp < cutoff_date:
            path = config.mailboxes_dir.joinpath(addr)
            assert path == user.maildir
            shutil.rmtree(path, ignore_errors=True)


def main():
    (cfgpath,) = sys.argv[1:]
    config = read_config(cfgpath)
    delete_inactive_users(config)
