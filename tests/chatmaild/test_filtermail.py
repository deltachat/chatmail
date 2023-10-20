from chatmaild.filtermail import check_encrypted, check_DATA, SendRateLimiter
import pytest


def test_reject_forged_from(mailgen):
    class envelope:
        mail_from = "bob@c3.testrun.org"
        rcpt_tos = ["somebody@c3.testrun.org"]

    # test that the filter lets good mail through
    envelope.content = mailgen.get_mail_data(
        "plain.eml", from_addr=envelope.mail_from
    ).as_bytes()
    assert not check_DATA(envelope=envelope)

    # test that the filter rejects forged mail
    envelope.content = mailgen.get_mail_data(
        "plain.eml", from_addr="forged@c3.testrun.org"
    ).as_bytes()
    error = check_DATA(envelope=envelope)
    assert "500" in error


def test_filtermail_no_encryption_detection(mailgen):
    msg = mailgen.get_mail_data("plain.eml")
    assert not check_encrypted(msg)

    # https://xkcd.com/1181/
    msg = mailgen.get_mail_data("fake-encrypted.eml")
    assert not check_encrypted(msg)


def test_filtermail_encryption_detection(mailgen):
    msg = mailgen.get_mail_data("encrypted.eml")
    assert check_encrypted(msg)

    # if the subject is not "..." it is not considered ac-encrypted
    msg.replace_header("Subject", "Click this link")
    assert not check_encrypted(msg)


def test_filtermail_mdn_is_not_encrypted(mailgen):
    msg = mailgen.get_mail_data("mdn.eml")
    assert not check_encrypted(msg)


def test_send_rate_limiter():
    limiter = SendRateLimiter()
    for i in range(100):
        if limiter.is_sending_allowed("some@example.org"):
            if i <= SendRateLimiter.MAX_USER_SEND_PER_MINUTE:
                continue
            pytest.fail("limiter didn't work")
        else:
            assert i == SendRateLimiter.MAX_USER_SEND_PER_MINUTE + 1
            break
