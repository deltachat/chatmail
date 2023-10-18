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


def test_reject_internal_forged_from(cmsetup, mailgen, lp, remote):
    user1, user2, user3 = cmsetup.gen_users(3)

    lp.sec("send encrypted message with forged from")
    print("envelope_from", user1.addr)
    print("message to inject:")
    msg = mailgen.get_encrypted(from_addr=user2.addr, to_addr=user3.addr)
    for line in msg.split("\n")[:4]:
        print(f"   {line}")

    remote_log = remote.iter_output("journalctl -t postfix/lmtp")
    user1.smtp.sendmail(from_addr=user1.addr, to_addrs=[user3.addr], msg=msg)

    for line in remote_log:
        print(line)
        if "500 invalid from" in line:
            break
    else:
        pytest.fail("remote postfix/filtermail failed to reject message")

    # also check that the forging-user got a non-delivery notice
    for flags, bmsg in user1.imap.fetch_all():
        message = bmsg.decode()
        if "Invalid FROM" in message and user2.addr in message:
            return
    pytest.fail("forged From did not cause rejection")
