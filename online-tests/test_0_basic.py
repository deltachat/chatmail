import smtplib
import pytest


def test_remote(remote, imap_or_smtp):
    lineproducer = remote.iter_output(imap_or_smtp.logcmd)
    imap_or_smtp.connect()
    assert imap_or_smtp.name in next(lineproducer)


def test_use_two_chatmailservers(cmfactory, maildomain2):
    ac1 = cmfactory.new_online_configuring_account(cache=False)
    cmfactory.switch_maildomain(maildomain2)
    ac2 = cmfactory.new_online_configuring_account(cache=False)
    cmfactory.bring_accounts_online()
    cmfactory.get_accepted_chat(ac1, ac2)
    domain1 = ac1.get_config("addr").split("@")[1]
    domain2 = ac2.get_config("addr").split("@")[1]
    assert domain1 != domain2


def test_reject_internal_forged_from(smtp, gencreds, mailgen, lp, imap):
    lp.sec("create forged user account")
    forged_user, password = gencreds()
    smtp.connect()
    smtp.login(forged_user, password)

    lp.sec("create TO user account")
    to_user, password = gencreds()
    smtp.connect()
    smtp.login(to_user, password)

    lp.sec("create account")
    login_user, login_password = gencreds()
    smtp.connect()
    smtp.login(login_user, login_password)

    lp.sec("send encrypted message with forged from")
    print("envelope_from", login_user)
    print("logged in as", login_user)

    print("injected mime message")
    msg = mailgen.get_encrypted(from_addr=forged_user, to_addr=to_user)
    for line in msg.split("\n")[:4]:
        print(f"   {line}")

    smtp.conn.sendmail(from_addr=login_user, to_addrs=[to_user], msg=msg)

    imap.connect()
    imap.login(login_user, login_password)
    imap.conn.select("Inbox")

    # detect mailer daemon rejection message
    status, results = imap.conn.fetch("1", "(RFC822)")
    assert status == "OK"
    for res in results:
        message = res[1].decode()
        if "Invalid FROM" in message and forged_user in message:
            return
    pytest.fail("forged From did not cause rejection")
