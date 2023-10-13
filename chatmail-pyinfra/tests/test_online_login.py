import pytest
import imaplib


@pytest.fixture
def conn():
    return connect("c1.testrun.org")


def login(conn, user, password):
    print("trying to login", user, password)
    conn.login(user, password)


def connect(host):
    print(f"connecting to {host}")
    conn = imaplib.IMAP4_SSL(host)
    return conn


def test_login_ok(conn):
    login(conn, "link2xt@c1.testrun.org", "Ahyei6ie")


def test_login_fail(conn):
    with pytest.raises(imaplib.IMAP4.error) as excinfo:
        login(conn, "link2xt@c1.testrun.org", "qweqwe")
    assert "AUTHENTICATIONFAILED" in str(excinfo)
