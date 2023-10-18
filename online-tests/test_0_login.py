import pytest
import smtplib


def test_login_basic_functioning(imap_or_smtp, gencreds, lp):
    """Test a) that an initial login creates a user automatically
    and b) verify we can also login a second time with the same password
    and c) that using a different password fails the login."""
    user, password = gencreds()
    lp.sec(f"login first time with {user} {password}")
    imap_or_smtp.connect()
    imap_or_smtp.login(user, password)
    lp.indent("success")

    lp.sec(f"reconnect and login second time {user} {password}")
    imap_or_smtp.connect()
    imap_or_smtp.login(user, password)
    imap_or_smtp.connect()
    lp.sec("success")

    lp.sec(f"reconnect and verify wrong password fails {user} ")
    imap_or_smtp.connect()
    with pytest.raises(imap_or_smtp.AuthError):
        imap_or_smtp.login(user, password + "wrong")


def test_login_same_password(imap_or_smtp, gencreds):
    """Test two different users logging in with the same password
    to ensure that authentication process does not confuse the users
    by using only the password hash as a key.
    """
    user1, password1 = gencreds()
    user2, _ = gencreds()
    imap_or_smtp.connect()
    imap_or_smtp.login(user1, password1)
    imap_or_smtp.connect()
    imap_or_smtp.login(user2, password1)
