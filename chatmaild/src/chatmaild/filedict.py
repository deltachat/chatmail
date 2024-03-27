import os
import logging
import marshal
import filelock
from contextlib import contextmanager


class FileDict:
    """Concurrency-safe multi-reader-single-writer Persistent Dict."""

    def __init__(self, path, timeout=5.0):
        self.path = path
        self.lock_path = path.with_name(path.name + ".lock")
        self.timeout = timeout

    @contextmanager
    def modify(self):
        try:
            with filelock.FileLock(self.lock_path, timeout=self.timeout):
                data = self.read()
                yield data
                write_path = self.path.with_suffix(".tmp")
                with write_path.open("wb") as f:
                    marshal.dump(data, f)
                os.rename(write_path, self.path)
        except filelock.Timeout:
            logging.warning("could not obtain lock, removing: %r", self.lock_path)
            os.remove(self.lock_path)
            with self.modify() as d:
                yield d

    def read(self):
        try:
            with self.path.open("rb") as f:
                return marshal.load(f)
        except FileNotFoundError:
            return {}
