"""
Remove inactive users
"""

import os
import shutil
import sys
import time
from pathlib import Path

from .config import read_config
from .database import Database

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


def delete_inactive_users(db, config, chunksize=100):
    cutoff_date = time.time() - config.delete_inactive_users_after * 86400
    pending = []

    def remove(userdir):
        shutil.rmtree(userdir, ignore_errors=True)
        pending.append(userdir.name)
        if len(pending) > chunksize:
            clear_pending()

    def clear_pending():
        with db.write_transaction() as conn:
            for user in pending:
                conn.execute("DELETE FROM users WHERE addr = ?", (user,))
        pending[:] = []

    for userdir in Path(config.mailboxes_dir).iterdir():
        if get_last_login_from_userdir(userdir) < cutoff_date:
            remove(userdir)

    clear_pending()


def main():
    (cfgpath,) = sys.argv[1:]
    config = read_config(cfgpath)
    db = Database(config.passdb_path)
    delete_inactive_users(db, config)
