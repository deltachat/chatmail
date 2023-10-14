import imaplib
import itertools
import pytest


@pytest.fixture
def imap():
    return ImapConn("c1.testrun.org")


class ImapConn:
    def __init__(self, host):
        self.host = host

    def connect(self):
        print(f"imap-connect {self.host}")
        self.conn = imaplib.IMAP4_SSL(self.host)

    def login(self, user, password):
        print(f"imap-login {user!r} {password!r}")
        self.conn.login(user, password)


@pytest.fixture
def gencreds():
    count = itertools.count()

    def gen():
        while 1:
            num = next(count)
            yield f"user{num}", f"password{num}"

    return lambda: next(gen())
