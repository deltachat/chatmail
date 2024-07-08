import crypt
import json
import logging
import os
import sys
import time
import shutil
from pathlib import Path
from socketserver import (
    StreamRequestHandler,
    ThreadingMixIn,
    UnixStreamServer,
)

from .config import Config, read_config
from .database import Database


def remove_users(db: Database, cutoff_date: int):
    with db.write_transaction() as conn:
        delete_query = "DELETE FROM users WHERE last_login <?"
        conn.execute(delete_query, (cutoff_date))


def remove_user_data(db: Database, cutoff_date: int, vmail_basedir: Path):
    """Collects all users where last_login < cutoff_date and deletes corresponding directories."""

    with db.write_transaction() as conn:
        select_query = "SELECT user FROM users WHERE last_login <?"
        cursor = conn.execute(select_query, (cutoff_date,))
        usernames = cursor.fetchall()

        for username in usernames:
            user_dir = vmail_basedir / username[0]
            if user_dir.exists() and user_dir.is_dir():
                shutil.rmtree(user_dir, ignore_errors=True)
                print(f"Deleted directory: {user_dir}")


def main():
    db = Database(sys.argv[2])
    config = read_config(sys.argv[3])
    today = round(int(time.time()) // 86400)

    cutoff_date = today - config.delete_accounts_after
    remove_user_data(db, cutoff_date)
