import json
import logging
import os
from contextlib import contextmanager
from random import randint

import filelock


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
            logging.warning(f"corrupt serialization state at: {self.path!r}")
            return {}


def write_bytes_atomic(path, content):
    rint = randint(0, 10000000)
    tmp = path.with_name(path.name + f".tmp-{rint}")
    tmp.write_bytes(content)
    os.rename(tmp, path)
