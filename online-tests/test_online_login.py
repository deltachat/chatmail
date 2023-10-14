import pytest
import imaplib
import smtplib


class TestDovecot:
    def test_login_ok(self, imap, gencreds):
        user, password = gencreds()
        imap.connect()
        imap.login(user, password)
        # verify it works on another connection
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


class TestPostfix:
    def test_login_ok(self, smtp, gencreds):
        user, password = gencreds()
        smtp.connect()
        smtp.login(user, password)
        # verify it works on another connection
        smtp.connect()
        smtp.login(user, password)

    def test_login_fail(self, smtp, gencreds):
        user, password = gencreds()
        smtp.connect()
        smtp.login(user, password)
        smtp.connect()
        with pytest.raises(smtplib.SMTPAuthenticationError) as excinfo:
            smtp.login(user, password + "wrong")
        assert excinfo.value.smtp_code == 535
        assert "authentication failed" in str(excinfo)


