import sqlite3
import contextlib
import time
from pathlib import Path


class DBError(Exception):
    """error during an operation on the database."""


class Connection:
    def __init__(self, sqlconn, write):
        self._sqlconn = sqlconn
        self._write = write

    def close(self):
        self._sqlconn.close()

    def commit(self):
        self._sqlconn.commit()

    def rollback(self):
        self._sqlconn.rollback()

    def execute(self, query, params=()):
        cur = self.cursor()
        try:
            cur.execute(query, params)
        except sqlite3.IntegrityError as e:
            raise DBError(e)
        return cur

    def cursor(self):
        return self._sqlconn.cursor()

    def create_user(self, addr: str, password: str):
        """Create a row in the users table."""
        self.execute("PRAGMA foreign_keys=on;")
        q = """INSERT INTO users (addr, password, last_login)
               VALUES (?, ?, ?)"""
        self.execute(q, (addr, password, int(time.time())))

    def get_user(self, addr: str) -> {}:
        """Get a row from the users table."""
        q = "SELECT addr, password, last_login from users WHERE addr = ?"
        row = self._sqlconn.execute(q, (addr,)).fetchone()
        result = {}
        if row:
            result = dict(
                user=row[0],
                password=row[1],
                last_login=row[2],
            )
        return result


class Database:
    def __init__(self, path: str):
        self.path = Path(path)
        self.ensure_tables()

    def _get_connection(
        self, write=False, transaction=False, closing=False
    ) -> Connection:
        # we let the database serialize all writers at connection time
        # to play it very safe (we don't have massive amounts of writes).
        mode = "ro"
        if write:
            mode = "rw"
        if not self.path.exists():
            mode = "rwc"
        uri = "file:%s?mode=%s" % (self.path, mode)
        sqlconn = sqlite3.connect(
            uri,
            timeout=60,
            isolation_level=None if transaction else "DEFERRED",
            uri=True,
        )

        # Enable Write-Ahead Logging to avoid readers blocking writers and vice versa.
        if write:
            sqlconn.execute("PRAGMA journal_mode=wal")

        if transaction:
            start_time = time.time()
            while 1:
                try:
                    sqlconn.execute("begin immediate")
                    break
                except sqlite3.OperationalError:
                    # another thread may be writing, give it a chance to finish
                    time.sleep(0.1)
                    if time.time() - start_time > 5:
                        # if it takes this long, something is wrong
                        raise
        conn = Connection(sqlconn, write=write)
        if closing:
            conn = contextlib.closing(conn)
        return conn

    @contextlib.contextmanager
    def write_transaction(self):
        conn = self._get_connection(closing=False, write=True, transaction=True)
        try:
            yield conn
        except Exception:
            conn.rollback()
            conn.close()
            raise
        else:
            conn.commit()
            conn.close()

    def read_connection(self, closing=True) -> Connection:
        return self._get_connection(closing=closing, write=False)

    def get_schema_version(self) -> int:
        with self.read_connection() as conn:
            dbversion = conn.execute("PRAGMA user_version;").fetchone()[0]
        return dbversion

    CURRENT_DBVERSION = 1

    def ensure_tables(self):
        with self.write_transaction() as conn:
            if self.get_schema_version() > 1:
                raise DBError(
                    "Database version is %s; downgrading database schema is not supported"
                    % (self.get_schema_version(),)
                )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    addr TEXT PRIMARY KEY,
                    password TEXT,
                    last_login INTEGER
                )
            """,
            )
            conn.execute("PRAGMA user_version=%s;" % (self.CURRENT_DBVERSION,))
