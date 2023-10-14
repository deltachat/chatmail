import os
import imaplib
import smtplib
import itertools
import pytest


@pytest.fixture
def maildomain():
    return os.environ.get("CHATMAIL_DOMAIN", "c1.testrun.org")


@pytest.fixture
def imap(maildomain):
    return ImapConn(maildomain)


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
def smtp(maildomain):
    return SmtpConn(maildomain)


class SmtpConn:
    def __init__(self, host):
        self.host = host

    def connect(self):
        print(f"smtp-connect {self.host}")
        self.conn = smtplib.SMTP_SSL(self.host)

    def login(self, user, password):
        print(f"smtp-login {user!r} {password!r}")
        self.conn.login(user, password)


@pytest.fixture
def gencreds(maildomain):
    count = itertools.count()

    def gen():
        while 1:
            num = next(count)
            yield f"user{num}@{maildomain}", f"password{num}"

    return lambda: next(gen())
