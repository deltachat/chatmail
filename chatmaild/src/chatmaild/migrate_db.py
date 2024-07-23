"""
migration code from old sqlite databases into per-maildir "password" files
where mtime reflects and is updated to be the "last-login" time.
"""
import logging
import os
import sqlite3
import sys

from chatmaild.config import read_config
from chatmaild.lastlogin import set_user_password, write_last_login_to_userdir


def get_all_rows(path):
    assert path.exists()
    uri = f"file:{path}?mode=ro"
    sqlconn = sqlite3.connect(uri, timeout=60, isolation_level="DEFERRED", uri=True)
    cur = sqlconn.cursor()
    cur.execute("SELECT * from users")
    rows = cur.fetchall()
    sqlconn.close()
    return rows


def migrate_from_db_to_maildir(config, chunking=10000):
    path = config.passdb_path
    if not path.exists():
        return

    all_rows = get_all_rows(path)

    rows = [row for row in all_rows if row[0][:3] not in ("ci-", "ac_")]

    logging.info(f"ignoring {len(all_rows)-len(rows)} CI accounts")
    logging.info(f"migrating {len(rows)} sqlite database passwords to user dirs")

    for i, row in enumerate(rows):
        addr = row[0]
        # don't transfer special/CI accounts (IOLO)
        if addr.startswith("echo@"):
            continue
        enc_password = row[1]
        set_user_password(config, addr, enc_password=enc_password)
        if len(row) == 3 and row[2]:
            homedir = config.mailboxes_dir.joinpath(addr)
            timestamp = int(row[2])
            write_last_login_to_userdir(homedir, timestamp)

        if i > 0 and i % chunking == 0:
            logging.info(f"migration-progress: {i} passwords transferred")

    logging.info("migration: all passwords migrated")
    oldpath = config.passdb_path.with_suffix(config.passdb_path.suffix + ".old")
    os.rename(config.passdb_path, oldpath)
    for path in config.passdb_path.parent.iterdir():
        if path.name.startswith(config.passdb_path.name + "-"):
            path.unlink()
    logging.info(f"migration: moved database to {oldpath!r}")


if __name__ == "__main__":
    config = read_config(sys.argv[1])
    logging.basicConfig(level=logging.INFO)
    migrate_from_db_to_maildir(config)
