from chatmaild.filtermail import check_encrypted, check_DATA, SendRateLimiter, check_mdn
import pytest


@pytest.fixture
def maildomain():
    # let's not depend on a real chatmail instance for the offline tests below
    return "chatmail.example.org"


def test_reject_forged_from(maildata, gencreds):
    class env:
        mail_from = gencreds()[0]
        rcpt_tos = [gencreds()[0]]

    # test that the filter lets good mail through
    env.content = maildata("plain.eml", from_addr=env.mail_from).as_bytes()
    assert not check_DATA(envelope=env)

    # test that the filter rejects forged mail
    env.content = maildata("plain.eml", from_addr="forged@c3.testrun.org").as_bytes()
    error = check_DATA(envelope=env)
    assert "500" in error


def test_filtermail_no_encryption_detection(maildata):
    msg = maildata("plain.eml")
    assert not check_encrypted(msg)

    # https://xkcd.com/1181/
    msg = maildata("fake-encrypted.eml")
    assert not check_encrypted(msg)


def test_filtermail_encryption_detection(maildata):
    msg = maildata("encrypted.eml")
    assert check_encrypted(msg)

    # if the subject is not "..." it is not considered ac-encrypted
    msg.replace_header("Subject", "Click this link")
    assert not check_encrypted(msg)


def test_filtermail_is_mdn(maildata, gencreds):
    from_addr = gencreds()[0]
    to_addr = gencreds()[0] + ".other"
    msg = maildata("mdn.eml", from_addr, to_addr)

    class env:
        mail_from = from_addr
        rcpt_tos = [to_addr]
        content = msg.as_bytes()

    assert check_mdn(msg, env)
    print(msg.as_string())
    assert not check_DATA(env)


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
        if limiter.is_sending_allowed("some@example.org"):
            if i <= SendRateLimiter.MAX_USER_SEND_PER_MINUTE:
                continue
            pytest.fail("limiter didn't work")
        else:
            assert i == SendRateLimiter.MAX_USER_SEND_PER_MINUTE + 1
            break
