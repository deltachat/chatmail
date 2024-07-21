import time

import pytest
from chatmaild.lastlogin import (
    LastLoginDictProxy,
    get_last_login_from_userdir,
    write_last_login_to_userdir,
)


@pytest.fixture
def testaddr():
    return "user.name@example.org"


def test_handle_dovecot_request_last_login(testaddr, example_config):
    dictproxy = LastLoginDictProxy(config=example_config)

    userdir = dictproxy.config.get_user_maildir(testaddr)

    # set last-login info for user
    tx = "1111"
    msg = f"B{tx}\t{testaddr}"
    res = dictproxy.handle_dovecot_request(msg)
    assert not res
    assert dictproxy.transactions == {tx: dict(addr=testaddr, res="O\n")}

    timestamp = int(time.time())
    msg = f"S{tx}\tshared/last-login/{testaddr}\t{timestamp}"
    res = dictproxy.handle_dovecot_request(msg)
    assert not res
    assert len(dictproxy.transactions) == 1
    read_timestamp = get_last_login_from_userdir(userdir)
    assert read_timestamp == timestamp // 86400 * 86400

    msg = f"C{tx}"
    res = dictproxy.handle_dovecot_request(msg)
    assert res == "O\n"
    assert len(dictproxy.transactions) == 0


def test_login_timestamp(testaddr, example_config):
    dictproxy = LastLoginDictProxy(config=example_config)
    userdir = dictproxy.config.get_user_maildir(testaddr)
    userdir.mkdir()
    write_last_login_to_userdir(userdir, timestamp=100000)
    assert get_last_login_from_userdir(userdir) == 86400

    write_last_login_to_userdir(userdir, timestamp=200000)
    assert get_last_login_from_userdir(userdir) == 86400 * 2
