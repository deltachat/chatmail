import os
import io
import random
import subprocess
import imaplib
import smtplib
import itertools
import pytest


def pytest_addoption(parser):
    parser.addoption(
        "--slow", action="store_true", default=False, help="also run slow tests"
    )


def pytest_runtest_setup(item):
    markers = list(item.iter_markers(name="slow"))
    if markers:
        if not item.config.getoption("--slow"):
            pytest.skip("skipping slow test, use --slow to run")


@pytest.fixture
def maildomain():
    domain = os.environ.get("CHATMAIL_DOMAIN")
    if not domain:
        pytest.skip("set CHATMAIL_DOMAIN to a ssh-reachable chatmail instance")
    return domain


@pytest.fixture
def chatmail_ssh(maildomain):
    domain = os.environ.get("CHATMAIL_SSH")
    if not domain:
        domain = maildomain
    return domain


def pytest_report_header():
    domain = os.environ.get("CHATMAIL_DOMAIN")
    if domain:
        text = f"chatmail test instance: {domain}"
        return ["-" * len(text), text, "-" * len(text)]


@pytest.fixture
def imap(maildomain):
    return ImapConn(maildomain)


class ImapConn:
    AuthError = imaplib.IMAP4.error

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
    AuthError = smtplib.SMTPAuthenticationError

    def __init__(self, host):
        self.host = host

    def connect(self):
        print(f"smtp-connect {self.host}")
        self.conn = smtplib.SMTP_SSL(self.host)

    def login(self, user, password):
        print(f"smtp-login {user!r} {password!r}")
        self.conn.login(user, password)


@pytest.fixture(params=["imap", "smtp"])
def imap_or_smtp(request):
    return request.getfixturevalue(request.param)


@pytest.fixture
def gencreds(maildomain):
    count = itertools.count()
    next(count)

    def gen():
        while 1:
            num = next(count)
            alphanumeric = "abcdefghijklmnopqrstuvwxyz1234567890"
            user = "".join(random.choices(alphanumeric, k=10))
            user = f"ac{num}_{user}"
            password = "".join(random.choices(alphanumeric, k=10))
            yield f"{user}@{maildomain}", f"{password}"

    return lambda: next(gen())


#
# Delta Chat testplugin re-use
# use the cmfactory fixture to get chatmail instance accounts
#


class ChatmailTestProcess:
    """Provider for chatmail instance accounts as used by deltachat.testplugin.acfactory"""

    def __init__(self, pytestconfig, maildomain, gencreds):
        self.pytestconfig = pytestconfig
        self.maildomain = maildomain
        self.gencreds = gencreds
        self._addr2files = {}

    def get_liveconfig_producer(self):
        while 1:
            user, password = self.gencreds()
            config = {
                "addr": user,
                "mail_pw": password,
            }
            # speed up account configuration
            config["mail_server"] = self.maildomain
            config["send_server"] = self.maildomain
            yield config

    def cache_maybe_retrieve_configured_db_files(self, cache_addr, db_target_path):
        pass

    def cache_maybe_store_configured_db_files(self, acc):
        pass


@pytest.fixture
def cmfactory(request, maildomain, gencreds, tmpdir, data):
    # cloned from deltachat.testplugin.amfactory
    pytest.importorskip("deltachat")
    from deltachat.testplugin import ACFactory

    testproc = ChatmailTestProcess(request.config, maildomain, gencreds)
    am = ACFactory(request=request, tmpdir=tmpdir, testprocess=testproc, data=data)
    yield am
    if hasattr(request.node, "rep_call") and request.node.rep_call.failed:
        if testproc.pytestconfig.getoption("--extra-info"):
            logfile = io.StringIO()
            am.dump_imap_summary(logfile=logfile)
            print(logfile.getvalue())
            # request.node.add_report_section("call", "imap-server-state", s)


@pytest.fixture
def dovelogreader(chatmail_ssh):
    def remote_reader():
        popen = subprocess.Popen(
            ["ssh", f"root@{chatmail_ssh}", "journalctl -f -u dovecot"],
            stdout=subprocess.PIPE,
        )
        while 1:
            yield popen.stdout.readline()

    return remote_reader
