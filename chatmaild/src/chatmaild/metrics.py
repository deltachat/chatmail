#!/usr/bin/env python3
import sys
import time
from pathlib import Path


def main(vmail_dir=None):
    if vmail_dir is None:
        vmail_dir = sys.argv[1]

    accounts = 0
    ci_accounts = 0

    for path in Path(vmail_dir).iterdir():
        accounts += 1
        if path.name[:3] in ("ci-", "ac_"):
            ci_accounts += 1

    timestamp = int(time.time() * 1000)
    print(f"accounts {accounts} {timestamp}")
    print(f"ci_accounts {ci_accounts} {timestamp}")


if __name__ == "__main__":
    main()
