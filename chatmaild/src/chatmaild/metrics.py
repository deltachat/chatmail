#!/usr/bin/env python3
from pathlib import Path
import time
import sys


def main():
    vmail_dir = sys.argv[1]
    accounts = 0
    ci_accounts = 0

    for path in Path(vmail_dir).iterdir():
        accounts += 1
        if path.name.startswith("ci-"):
            ci_accounts += 1

    timestamp = int(time.time() * 1000)
    print(f"accounts {accounts} {timestamp}")
    print(f"ci_accounts {ci_accounts} {timestamp}")


if __name__ == "__main__":
    main()
