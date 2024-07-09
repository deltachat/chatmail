"""
Remove inactive users
"""

import shutil
import sys
import time

from .config import read_config
from .database import Database
from .doveauth import iter_userdb_lastlogin_before


def remove_user(db, config, user):
    user_mail_dir = config.get_user_maildir(user)
    shutil.rmtree(user_mail_dir, ignore_errors=True)
    with db.write_transaction() as conn:
        conn.execute("DELETE FROM users WHERE addr = ?", (user,))


def delete_inactive_users(db, config):
    cutoff_date = time.time() - config.delete_inactive_users_after * 86400
    for user in iter_userdb_lastlogin_before(db, cutoff_date):
        remove_user(db, config, user)
        print(f"Deleted user: {user}")


def main():
    db = Database(sys.argv[1])
    config = read_config(sys.argv[2])
    delete_inactive_users(db, config)
