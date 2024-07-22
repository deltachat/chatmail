"""
Remove inactive users
"""

import shutil
import sys
import time

from .config import read_config
from .lastlogin import get_last_login_from_userdir


def delete_inactive_users(config):
    cutoff_date = time.time() - config.delete_inactive_users_after * 86400
    for userdir in config.mailboxes_dir.iterdir():
        if get_last_login_from_userdir(userdir) < cutoff_date:
            shutil.rmtree(userdir, ignore_errors=True)


def main():
    (cfgpath,) = sys.argv[1:]
    config = read_config(cfgpath)
    delete_inactive_users(config)
