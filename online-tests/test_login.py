import pytest
import imaplib


class TestDovecot:
    def test_login_ok(self, imap, gencreds):
        user, password = gencreds()
        imap.connect()
        imap.login(user, password)

    def test_login_fail(self, imap, gencreds):
        user, password = gencreds()
        imap.connect()
        imap.login(user, password)
        imap.connect()
        with pytest.raises(imaplib.IMAP4.error) as excinfo:
            imap.login(user, password + "wrong")
        assert "AUTHENTICATIONFAILED" in str(excinfo)
