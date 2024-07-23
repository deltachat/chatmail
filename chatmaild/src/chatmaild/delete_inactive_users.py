"""
Remove inactive users
"""

import shutil
import sys
import time

from .config import read_config
from .database import Database
from .doveauth import iter_userdb_lastlogin_before


def delete_inactive_users(db, config, CHUNK=100):
    cutoff_date = time.time() - config.delete_inactive_users_after * 86400

    old_users = iter_userdb_lastlogin_before(db, cutoff_date)
    chunks = (old_users[i : i + CHUNK] for i in range(0, len(old_users), CHUNK))
    for sublist in chunks:
        for user in sublist:
            user_mail_dir = config.get_user_maildir(user)
            shutil.rmtree(user_mail_dir, ignore_errors=True)

        with db.write_transaction() as conn:
            for user in sublist:
                conn.execute("DELETE FROM users WHERE addr = ?", (user,))


def main():
    (cfgpath,) = sys.argv[1:]
    config = read_config(cfgpath)
    db = Database(config.passdb_path)
    delete_inactive_users(db, config)
