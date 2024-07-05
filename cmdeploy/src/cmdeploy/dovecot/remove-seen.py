#!/usr/bin/env python3
"""Remove seen messages that are older than two days
if maildir has more than 80 MB of messages."""
import sys
import time
from pathlib import Path


def getdirsize(path):
    return sum(f.stat().st_size for f in path.glob("**/*") if f.is_file())


def parse_dovecot_seen(path):
    return "S" in path.name.split(":2,")[-1]


def main():
    now = time.time()

    mailhome = Path(sys.argv[1])

    for p in mailhome.iterdir():
        dirsize = getdirsize(p / "cur") + getdirsize(p / "new")
        if dirsize < 80000000:
            continue

        removed_bytes = 0
        for mailpath in (p / "cur").iterdir():
            seen = parse_dovecot_seen(mailpath)
            stat = mailpath.stat()
            size = stat.st_size
            if seen and now > stat.st_mtime + 2 * 24 * 3600:
                removed_bytes += size
                mailpath.unlink(missing_ok=True)

        if removed_bytes > 0:
            (p / "maildirsize").unlink(missing_ok=True)


if __name__ == "__main__":
    main()
