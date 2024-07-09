from time import time as now

from chatmaild.delete_inactive_users import delete_inactive_users
from chatmaild.doveauth import lookup_passdb


def test_remove_stale_users(db, example_config):
    old = now() - (example_config.delete_inactive_users_after * 86400) - 1000
    new = old + 1001

    def create_user(addr, last_login):
        lookup_passdb(db, example_config, addr, "q9mr3faue", last_login=last_login)
        md = example_config.get_user_maildir(addr)
        md.mkdir(parents=True)
        md.joinpath("cur").mkdir()
        md.joinpath("cur", "something").mkdir()

    for i in range(10):
        create_user(f"oldold{i:03}@chat.example.org", last_login=old)

    remain = []
    for i in range(5):
        create_user(f"newnew{i:03}@chat.example.org", last_login=new)

    udir = example_config.get_user_maildir("oldold001@chat.example.org")
    assert udir.exists()

    delete_inactive_users(db, example_config)

    for p in udir.parent.iterdir():
        assert not p.name.startswith("old")

    for addr in remain:
        assert example_config.get_user_maildir(addr).exists()
