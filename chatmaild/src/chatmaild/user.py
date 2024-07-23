import logging
import os

import filelock


def get_daytimestamp(timestamp) -> int:
    return int(timestamp) // 86400 * 86400


class User:
    def __init__(self, maildir, addr, password_path, uid, gid):
        self.maildir = maildir
        self.addr = addr
        self.password_path = password_path
        self.uid = uid
        self.gid = gid

    @property
    def can_track(self):
        return "@" in self.addr and not self.addr.startswith("echo@")

    def get_userdb_dict(self):
        """Return a non-empty dovecot 'userdb' style dict
        if the user has an existing non-empty password"""
        try:
            pw = self.password_path.read_text()
        except FileNotFoundError:
            logging.error(f"password not set for: {self.addr}")
            return {}

        if not pw:
            logging.error(f"password is empty for: {self.addr}")
            return {}

        home = str(self.maildir)
        return dict(addr=self.addr, home=home, uid=self.uid, gid=self.gid, password=pw)

    def set_password(self, enc_password):
        """Set the specified password for this user.

        If called concurrently from multiple threads
        the last password set call will be persisted.
        """
        self.maildir.mkdir(exist_ok=True)
        lock_path = self.maildir.joinpath("password.lock")
        password = enc_password.encode("ascii")

        with filelock.FileLock(lock_path):
            try:
                self.password_path.write_bytes(password)
            except PermissionError:
                if not self.addr.startswith("echo@"):
                    logging.error(f"could not write password for: {self.addr}")
                    raise

    def set_last_login_timestamp(self, timestamp):
        """Track login time with daily granularity
        to minimize touching files and to minimize metadata leakage."""
        if not self.can_track:
            return
        try:
            mtime = int(os.stat(self.password_path).st_mtime)
        except FileNotFoundError:
            logging.error(f"Can not get last login timestamp for {self.addr}")
            return

        timestamp = get_daytimestamp(timestamp)
        if mtime != timestamp:
            os.utime(self.password_path, (timestamp, timestamp))

    def get_last_login_timestamp(self):
        if self.can_track:
            try:
                return int(self.password_path.stat().st_mtime)
            except FileNotFoundError:
                pass
