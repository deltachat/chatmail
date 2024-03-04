from chatmaild.filtermail import (
    check_encrypted,
    BeforeQueueHandler,
    SendRateLimiter,
    check_mdn,
)

import pytest


@pytest.fixture
def maildomain():
    # let's not depend on a real chatmail instance for the offline tests below
    return "chatmail.example.org"


@pytest.fixture
def handler(make_config, maildomain):
    config = make_config(maildomain)
    return BeforeQueueHandler(config)


def test_reject_forged_from(maildata, gencreds, handler):
    class env:
        mail_from = gencreds()[0]
        rcpt_tos = [gencreds()[0]]

    # test that the filter lets good mail through
    to_addr = gencreds()[0]
    env.content = maildata(
        "plain.eml", from_addr=env.mail_from, to_addr=to_addr
    ).as_bytes()

    assert not handler.check_DATA(envelope=env)

    # test that the filter rejects forged mail
    env.content = maildata(
        "plain.eml", from_addr="forged@c3.testrun.org", to_addr=to_addr
    ).as_bytes()
    error = handler.check_DATA(envelope=env)
    assert "500" in error


def test_filtermail_no_encryption_detection(maildata):
    msg = maildata(
        "plain.eml", from_addr="some@example.org", to_addr="other@example.org"
    )
    assert not check_encrypted(msg)

    # https://xkcd.com/1181/
    msg = maildata(
        "fake-encrypted.eml", from_addr="some@example.org", to_addr="other@example.org"
    )
    assert not check_encrypted(msg)


def test_filtermail_encryption_detection(maildata):
    msg = maildata("encrypted.eml", from_addr="1@example.org", to_addr="2@example.org")
    assert check_encrypted(msg)

    # if the subject is not "..." it is not considered ac-encrypted
    msg.replace_header("Subject", "Click this link")
    assert not check_encrypted(msg)


def test_filtermail_encryption_detection_k9subject(maildata):
    msg = maildata(
        "encrypted-k9.eml", from_addr="1@example.org", to_addr="2@example.org"
    )
    assert check_encrypted(msg)

    # if the subject is not "..." it is not considered ac-encrypted
    msg.replace_header("Subject", "Click this link")
    assert not check_encrypted(msg)


def test_filtermail_is_mdn(maildata, gencreds, handler):
    from_addr = gencreds()[0]
    to_addr = gencreds()[0] + ".other"
    msg = maildata("mdn.eml", from_addr, to_addr)

    class env:
        mail_from = from_addr
        rcpt_tos = [to_addr]
        content = msg.as_bytes()

    assert check_mdn(msg, env)
    print(msg.as_string())

    assert not handler.check_DATA(env)


def test_filtermail_to_multiple_recipients_no_mdn(maildata, gencreds):
    from_addr = gencreds()[0]
    to_addr = gencreds()[0] + ".other"
    thirdaddr = gencreds()[0]
    msg = maildata("mdn.eml", from_addr, to_addr)

    class env:
        mail_from = from_addr
        rcpt_tos = [to_addr, thirdaddr]
        content = msg.as_bytes()

    assert not check_mdn(msg, env)


def test_send_rate_limiter():
    limiter = SendRateLimiter()
    for i in range(100):
        if limiter.is_sending_allowed("some@example.org", 10):
            if i <= 10:
                continue
            pytest.fail("limiter didn't work")
        else:
            assert i == 11
            break


def test_excempt_privacy(maildata, gencreds, handler):
    from_addr = gencreds()[0]
    to_addr = "privacy@testrun.org"
    handler.config.passthrough_recipients = [to_addr]
    false_to = "privacy@something.org"

    msg = maildata("plain.eml", from_addr, to_addr)

    class env:
        mail_from = from_addr
        rcpt_tos = [to_addr]
        content = msg.as_bytes()

    # assert that None/no error is returned
    assert not handler.check_DATA(envelope=env)

    class env2:
        mail_from = from_addr
        rcpt_tos = [to_addr, false_to]
        content = msg.as_bytes()

    assert "500" in handler.check_DATA(envelope=env2)


def test_passthrough_senders(gencreds, handler, maildata):
    acc1 = gencreds()[0]
    to_addr = "recipient@something.org"
    handler.config.passthrough_senders = [acc1]

    msg = maildata("plain.eml", acc1, to_addr)

    class env:
        mail_from = acc1
        rcpt_tos = to_addr
        content = msg.as_bytes()

    # assert that None/no error is returned
    assert not handler.check_DATA(envelope=env)
