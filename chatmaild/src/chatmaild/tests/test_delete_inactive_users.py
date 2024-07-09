import time

from chatmaild.delete_inactive_users import delete_inactive_users
from chatmaild.doveauth import lookup_passdb


def test_remove_stale_users(db, example_config):
    new = time.time()
    old = new - (example_config.delete_inactive_users_after * 86400) - 1

    def create_user(addr, last_login):
        lookup_passdb(db, example_config, addr, "q9mr3faue", last_login=last_login)
        md = example_config.get_user_maildir(addr)
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
        assert example_config.get_user_maildir(addr).exists()

    delete_inactive_users(db, example_config)

    for p in example_config.mail_basedir.iterdir():
        assert not p.name.startswith("old")

    for addr in to_remove:
        with db.read_connection() as conn:
            assert not conn.get_user(addr)
            assert not example_config.get_user_maildir(addr).exists()

    for addr in remain:
        assert example_config.get_user_maildir(addr).exists()
        with db.read_connection() as conn:
            assert conn.get_user(addr)
