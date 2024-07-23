import time

from chatmaild.delete_inactive_users import delete_inactive_users
from chatmaild.doveauth import AuthDictProxy
from chatmaild.lastlogin import get_last_login_from_userdir, write_last_login_to_userdir


def test_login_timestamps(tmp_path):
    userdir = tmp_path.joinpath("someuser@chat.example.org")
    userdir.mkdir()
    userdir.joinpath("password").touch()
    write_last_login_to_userdir(userdir, timestamp=100000)
    assert get_last_login_from_userdir(userdir) == 86400

    write_last_login_to_userdir(userdir, timestamp=200000)
    assert get_last_login_from_userdir(userdir) == 86400 * 2

    write_last_login_to_userdir(userdir, timestamp=200000)
    assert get_last_login_from_userdir(userdir) == 86400 * 2


def test_delete_skips_non_email_dir(example_config):
    userdir = example_config.get_user_maildir("something")
    userdir.mkdir()
    get_last_login_from_userdir(userdir)
    assert not list(userdir.iterdir())


def test_delete_inactive_users(example_config):
    new = time.time()
    old = new - (example_config.delete_inactive_users_after * 86400) - 1
    dictproxy = AuthDictProxy(example_config)

    def create_user(addr, last_login):
        dictproxy.lookup_passdb(addr, "q9mr3faue")
        md = example_config.get_user_maildir(addr)
        md.joinpath("cur").mkdir()
        md.joinpath("cur", "something").mkdir()
        write_last_login_to_userdir(md, timestamp=last_login)

    # create some stale and some new accounts
    to_remove = []
    for i in range(150):
        addr = f"oldold{i:03}@chat.example.org"
        create_user(addr, last_login=old)
        to_remove.append(addr)

    remain = []
    for i in range(5):
        addr = f"newnew{i:03}@chat.example.org"
        create_user(addr, last_login=new)
        remain.append(addr)

    # check pre and post-conditions for delete_inactive_users()

    for addr in to_remove:
        assert example_config.get_user_maildir(addr).exists()

    delete_inactive_users(example_config)

    for p in example_config.mailboxes_dir.iterdir():
        assert not p.name.startswith("old")

    for addr in to_remove:
        assert not example_config.get_user_maildir(addr).exists()

    for addr in remain:
        userdir = example_config.get_user_maildir(addr)
        assert userdir.exists()
        assert userdir.joinpath("password").read_text()
