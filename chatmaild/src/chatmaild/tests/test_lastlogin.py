import time

import pytest
from chatmaild.doveauth import AuthDictProxy
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

    authproxy = AuthDictProxy(config=example_config)
    authproxy.lookup_passdb(testaddr, "1l2k3j1l2k3jl123")

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


def test_handle_dovecot_request_last_login_echobot(example_config):
    dictproxy = LastLoginDictProxy(config=example_config)

    authproxy = AuthDictProxy(config=example_config)
    testaddr = f"echo@{example_config.mail_domain}"
    authproxy.lookup_passdb(testaddr, "ignore")
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
    assert read_timestamp == time.time() // 86400 * 86400


def test_login_timestamp(testaddr, example_config):
    dictproxy = LastLoginDictProxy(config=example_config)
    authproxy = AuthDictProxy(config=example_config)
    authproxy.lookup_passdb(testaddr, "1l2k3j1l2k3jl123")
    userdir = dictproxy.config.get_user_maildir(testaddr)
    write_last_login_to_userdir(userdir, timestamp=100000)
    assert get_last_login_from_userdir(userdir) == 86400

    write_last_login_to_userdir(userdir, timestamp=200000)
    assert get_last_login_from_userdir(userdir) == 86400 * 2
