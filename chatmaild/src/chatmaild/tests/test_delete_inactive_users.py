import time
from pathlib import Path

from chatmaild.delete_inactive_users import delete_inactive_users
from chatmaild.doveauth import lookup_passdb


def test_remove_stale_users(db, example_config):
    new = time.time()
    old = new - (example_config.delete_inactive_users_after * 86400) - 1

    def get_user_path(addr):
        return Path(example_config.get_user_maildir(addr))

    def create_user(addr, last_login):
        lookup_passdb(db, example_config, addr, "q9mr3faue", last_login=last_login)
        md = get_user_path(addr)
        md.mkdir(parents=True)
        md.joinpath("cur").mkdir()
        md.joinpath("cur", "something").mkdir()

    # create some stale and some new accounts
    to_remove = []
    for i in range(150):
        addr = f"oldold{i:03}@chat.example.org"
        create_user(addr, last_login=old)
        with db.read_connection() as conn:
            assert conn.get_user(addr)
        to_remove.append(addr)

    remain = []
    for i in range(5):
        addr = f"newnew{i:03}@chat.example.org"
        create_user(addr, last_login=new)
        remain.append(addr)

    # check pre and post-conditions for delete_inactive_users()

    for addr in to_remove:
        assert get_user_path(addr).exists()

    delete_inactive_users(db, example_config)

    for p in Path(example_config.mailboxes_dir).iterdir():
        assert not p.name.startswith("old")

    for addr in to_remove:
        assert not get_user_path(addr).exists()
        with db.read_connection() as conn:
            assert not conn.get_user(addr)

    for addr in remain:
        assert get_user_path(addr).exists()
        with db.read_connection() as conn:
            assert conn.get_user(addr)
