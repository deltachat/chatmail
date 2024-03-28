import os
import logging
import json
import filelock
from contextlib import contextmanager


class FileDict:
    """Concurrency-safe multi-reader/single-writer persistent dict."""

    def __init__(self, path):
        self.path = path
        self.lock_path = path.with_name(path.name + ".lock")

    @contextmanager
    def modify(self):
        # the OS will release the lock if the process dies,
        # and the contextmanager will otherwise guarantee release
        with filelock.FileLock(self.lock_path):
            data = self.read()
            yield data
            write_path = self.path.with_name(self.path.name + ".tmp")
            with write_path.open("w") as f:
                json.dump(data, f)
            os.rename(write_path, self.path)

    def read(self):
        try:
            with self.path.open("r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception:
            logging.warning("corrupt marshal data at: %r", self.path)
            return {}
