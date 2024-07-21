"""
Remove inactive users
"""

import shutil
import sys
import time

from .config import read_config
from .database import Database
from .lastlogin import get_last_login_from_userdir


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
        pending.clear()

    for userdir in config.mailboxes_dir.iterdir():
        if get_last_login_from_userdir(userdir) < cutoff_date:
            remove(userdir)

    clear_pending()


def main():
    (cfgpath,) = sys.argv[1:]
    config = read_config(cfgpath)
    db = Database(config.passdb_path)
    delete_inactive_users(db, config)
