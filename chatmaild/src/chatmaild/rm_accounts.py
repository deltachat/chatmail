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
    db.connect()
    try:
        delete_query = "DELETE FROM users WHERE last_login <?"
        db.execute_query(delete_query, (cutoff_date))
        db.commit_changes()
    finally:
        db.close()


def remove_user_data(db: Database, cutoff_date: int, dir: Path):
    """Collects all users where last_login < cutoff_date and deletes corresponding directories."""
    db.connect()

    try:
        select_query = "SELECT user FROM users WHERE last_login <?"
        cursor = db.execute_query(select_query, (cutoff_date,))
        usernames = cursor.fetchall()

        for username in usernames:
            user_dir = dir / username[0]
            if user_dir.exists() and user_dir.is_dir():
                shutil.rmtree(user_dir)
                print(f"Deleted directory: {user_dir}")

    finally:
        db.close()


def main():
    db = Database(sys.argv[2])
    config = read_config(sys.argv[3])
    today = round(int(time.time()) // 86400)

    cutoff_date = today - config.delete_accounts_after
    remove_user_data(db, cutoff_date)
