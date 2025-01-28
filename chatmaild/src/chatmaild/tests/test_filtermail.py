import pytest

from chatmaild.filtermail import (
    BeforeQueueHandler,
    SendRateLimiter,
    check_armored_payload,
    check_encrypted,
    common_encrypted_subjects,
    is_securejoin,
)


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


def test_filtermail_securejoin_detection(maildata):
    msg = maildata(
        "securejoin-vc.eml", from_addr="some@example.org", to_addr="other@example.org"
    )
    assert is_securejoin(msg)

    msg = maildata(
        "securejoin-vc-fake.eml",
        from_addr="some@example.org",
        to_addr="other@example.org",
    )
    assert not is_securejoin(msg)


def test_filtermail_encryption_detection(maildata):
    for subject in common_encrypted_subjects:
        msg = maildata(
            "encrypted.eml",
            from_addr="1@example.org",
            to_addr="2@example.org",
            subject=subject,
        )
        assert check_encrypted(msg)

    # if the subject is not a known encrypted subject value, it is not considered ac-encrypted
    msg.replace_header("Subject", "Click this link")
    assert not check_encrypted(msg)


def test_filtermail_no_literal_packets(maildata):
    """Test that literal OpenPGP packet is not considered an encrypted mail."""
    msg = maildata("literal.eml", from_addr="1@example.org", to_addr="2@example.org")
    assert not check_encrypted(msg)


def test_filtermail_unencrypted_mdn(maildata, gencreds):
    """Unencrypted MDNs should not pass."""
    from_addr = gencreds()[0]
    to_addr = gencreds()[0] + ".other"
    msg = maildata("mdn.eml", from_addr=from_addr, to_addr=to_addr)

    assert not check_encrypted(msg)


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

    msg = maildata("plain.eml", from_addr=from_addr, to_addr=to_addr)

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


def test_passthrough_domains(maildata, gencreds, handler):
    from_addr = gencreds()[0]
    to_addr = "privacy@x.y.z"
    handler.config.passthrough_recipients = ["@x.y.z"]
    false_to = "something@x.y"

    msg = maildata("plain.eml", from_addr=from_addr, to_addr=to_addr)

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

    msg = maildata("plain.eml", from_addr=acc1, to_addr=to_addr)

    class env:
        mail_from = acc1
        rcpt_tos = to_addr
        content = msg.as_bytes()

    # assert that None/no error is returned
    assert not handler.check_DATA(envelope=env)


def test_check_armored_payload():
    payload = """-----BEGIN PGP MESSAGE-----\r
\r
wU4DSqFx0d1yqAoSAQdAYkX/ZN/Az4B0k7X47zKyWrXxlDEdS3WOy0Yf2+GJTFgg\r
Zk5ql0mLG8Ze+ZifCS0XMO4otlemSyJ0K1ZPdFMGzUDBTgNqzkFabxXoXRIBB0AM\r
755wlX41X6Ay3KhnwBq7yEqSykVH6F3x11iHPKraLCAGZoaS8bKKNy/zg5slda1X\r
pt14b4aC1VwtSnYhcRRELNLD/wE2TFif+g7poMmFY50VyMPLYjVP96Z5QCT4+z4H\r
Ikh/pRRN8S3JNMrRJHc6prooSJmLcx47Y5un7VFy390MsJ+LiUJuQMDdYWRAinfs\r
Ebm89Ezjm7F03qbFPXE0X4ZNzVXS/eKO0uhJQdiov/vmbn41rNtHmNpqjaO0vi5+\r
sS9tR7yDUrIXiCUCN78eBLVioxtktsPZm5cDORbQWzv+7nmCEz9/JowCUcBVdCGn\r
1ofOaH82JCAX/cRx08pLaDNj6iolVBsi56Dd+2bGxJOZOG2AMcEyz0pXY0dOAJCD\r
iUThcQeGIdRnU3j8UBcnIEsjLu2+C+rrwMZQESMWKnJ0rnqTk0pK5kXScr6F/L0L\r
UE49ccIexNm3xZvYr5drszr6wz3Tv5fdue87P4etBt90gF/Vzknck+g1LLlkzZkp\r
d8dI0k2tOSPjUbDPnSy1x+X73WGpPZmj0kWT+RGvq0nH6UkJj3AQTG2qf1T8jK+3\r
rTp3LR9vDkMwDjX4R8SA9c0wdnUzzr79OYQC9lTnzcx+fM6BBmgQ2GrS33jaFLp7\r
L6/DFpCl5zhnPjM/2dKvMkw/Kd6XS/vjwsO405FQdjSDiQEEAZA+ZvAfcjdccbbU\r
yCO+x0QNdeBsufDVnh3xvzuWy4CICdTQT4s1AWRPCzjOj+SGmx5WqCLWfsd8Ma0+\r
w/C7SfTYu1FDQILLM+llpq1M/9GPley4QZ8JQjo262AyPXsPF/OW48uuZz0Db1xT\r
Yh4iHBztj4VSdy7l2+IyaIf7cnL4EEBFxv/MwmVDXvDlxyvfAfIsd3D9SvJESzKZ\r
VWDYwaocgeCN+ojKu1p885lu1EfRbX3fr3YO02K5/c2JYDkc0Py0W3wUP/J1XUax\r
pbKpzwlkxEgtmzsGqsOfMJqBV3TNDrOA2uBsa+uBqP5MGYLZ49S/4v/bW9I01Cr1\r
D2ZkV510Y1Vgo66WlP8mRqOTyt/5WRhPD+MxXdk67BNN/PmO6tMlVoJDuk+XwWPR\r
t2TvNaND/yabT9eYI55Og4fzKD6RIjouUX8DvKLkm+7aXxVs2uuLQ3Jco3O82z55\r
dbShU1jYsrw9oouXUz06MHPbkdhNbF/2hfhZ2qA31sNeovJw65iUv7sDKX3LVWgJ\r
10jlywcDwqlU8CO7WC9lGixYTbnOkYZpXCGEl8e6Jbs79l42YFo4ogYpFK1NXFhV\r
kOXRmDf/wmfj+c/ld3L2PkvwlgofhCudOQknZbo3ub1gjiTn7L+lMGHIj/3suMIl\r
ID4EUxAXScIM1ZEz2fjtW5jATlqYcLjLTbf/olw6HFyPNH+9IssqXeZNKnGwPUB9\r
3lTXsg0tpzl+x7F/2WjEw1DSNhjC0KnHt1vEYNMkUGDGFdN9y3ERLqX/FIgiASUb\r
bTvAVupnAK3raBezGmhrs6LsQtLS9P0VvQiLU3uDhMqw8Z4SISLpcD+NnVBHzQqm\r
6W5Qn/8xsCL6av18yUVTi2G3igt3QCNoYx9evt2ZcIkNoyyagUVjfZe5GHXh8Dnz\r
GaBXW/hg3HlXLRGaQu4RYCzBMJILcO25OhZOg6jbkCLiEexQlm2e9krB5cXR49Al\r
UN4fiB0KR9JyG2ayUdNJVkXZSZLnHyRgiaadlpUo16LVvw==\r
=b5Kp\r
-----END PGP MESSAGE-----\r
\r
"""

    assert check_armored_payload(payload) == True

    payload = """-----BEGIN PGP MESSAGE-----\r
\r
HELLOWORLD
-----END PGP MESSAGE-----\r
\r
"""
    assert check_armored_payload(payload) == False

    payload = """-----BEGIN PGP MESSAGE-----\r
\r
=njUN
-----END PGP MESSAGE-----\r
\r
"""
    assert check_armored_payload(payload) == False
