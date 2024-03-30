import io
import pytest
import requests

from chatmaild.metadata import (
    handle_dovecot_request,
    handle_dovecot_protocol,
    Notifier,
)


@pytest.fixture
def notifier(tmp_path):
    vmail_dir = tmp_path.joinpath("vmaildir")
    vmail_dir.mkdir()
    return Notifier(vmail_dir)


@pytest.fixture
def testaddr():
    return "user.name@example.org"


@pytest.fixture
def testaddr2():
    return "user2@example.org"


@pytest.fixture
def token():
    return "01234"


def get_mocked_requests(statuslist):
    class ReqMock:
        requests = []

        def post(self, url, data, timeout):
            self.requests.append((url, data, timeout))
            res = statuslist.pop(0)
            if isinstance(res, Exception):
                raise res

            class Result:
                status_code = res

            return Result()

    return ReqMock()


def test_notifier_persistence(tmp_path, testaddr, testaddr2):
    notifier1 = Notifier(tmp_path)
    notifier2 = Notifier(tmp_path)
    assert not notifier1.get_tokens(testaddr)
    assert not notifier2.get_tokens(testaddr)

    notifier1.add_token(testaddr, "01234")
    notifier1.add_token(testaddr2, "456")
    assert notifier2.get_tokens(testaddr) == ["01234"]
    assert notifier2.get_tokens(testaddr2) == ["456"]
    notifier2.remove_token(testaddr, "01234")
    assert not notifier1.get_tokens(testaddr)
    assert notifier1.get_tokens(testaddr2) == ["456"]


def test_remove_nonexisting(tmp_path, testaddr):
    notifier1 = Notifier(tmp_path)
    notifier1.add_token(testaddr, "123")
    notifier1.remove_token(testaddr, "1l23k1l2k3")
    assert notifier1.get_tokens(testaddr) == ["123"]


def test_notifier_delete_without_set(notifier, testaddr):
    notifier.remove_token(testaddr, "123")
    assert not notifier.get_tokens(testaddr)


def test_handle_dovecot_request_lookup_fails(notifier, testaddr):
    res = handle_dovecot_request(f"Lpriv/123/chatmail\t{testaddr}", {}, notifier)
    assert res == "N\n"


def test_handle_dovecot_request_happy_path(notifier, testaddr, token):
    transactions = {}

    # set device token in a transaction
    tx = "1111"
    msg = f"B{tx}\t{testaddr}"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert not res and not notifier.get_tokens(testaddr)
    assert transactions == {tx: dict(addr=testaddr, res="O\n")}

    msg = f"S{tx}\tpriv/guid00/devicetoken\t{token}"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert not res
    assert len(transactions) == 1
    assert notifier.get_tokens(testaddr) == [token]

    msg = f"C{tx}"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert res == "O\n"
    assert len(transactions) == 0
    assert notifier.get_tokens(testaddr) == [token]

    # trigger notification for incoming message
    tx2 = "2222"
    assert handle_dovecot_request(f"B{tx2}\t{testaddr}", transactions, notifier) is None
    msg = f"S{tx2}\tpriv/guid00/messagenew"
    assert handle_dovecot_request(msg, transactions, notifier) is None
    assert notifier.retry_queues[0].get()[1] == token
    assert handle_dovecot_request(f"C{tx2}", transactions, notifier) == "O\n"
    assert not transactions
    assert notifier.notification_dir.joinpath(token).exists()


def test_handle_dovecot_protocol_set_devicetoken(notifier):
    rfile = io.BytesIO(
        b"\n".join(
            [
                b"HELLO",
                b"Btx00\tuser@example.org",
                b"Stx00\tpriv/guid00/devicetoken\t01234",
                b"Ctx00",
            ]
        )
    )
    wfile = io.BytesIO()
    handle_dovecot_protocol(rfile, wfile, notifier)
    assert wfile.getvalue() == b"O\n"
    assert notifier.get_tokens("user@example.org") == ["01234"]


def test_handle_dovecot_protocol_set_get_devicetoken(notifier):
    rfile = io.BytesIO(
        b"\n".join(
            [
                b"HELLO",
                b"Btx00\tuser@example.org",
                b"Stx00\tpriv/guid00/devicetoken\t01234",
                b"Ctx00",
            ]
        )
    )
    wfile = io.BytesIO()
    handle_dovecot_protocol(rfile, wfile, notifier)
    assert notifier.get_tokens("user@example.org") == ["01234"]
    assert wfile.getvalue() == b"O\n"

    rfile = io.BytesIO(
        b"\n".join([b"HELLO", b"Lpriv/0123/devicetoken\tuser@example.org"])
    )
    wfile = io.BytesIO()
    handle_dovecot_protocol(rfile, wfile, notifier)
    assert wfile.getvalue() == b"O01234\n"


def test_handle_dovecot_protocol_iterate(notifier):
    rfile = io.BytesIO(
        b"\n".join(
            [
                b"H",
                b"I9\t0\tpriv/5cbe730f146fea6535be0d003dd4fc98/\tci-2dzsrs@nine.testrun.org",
            ]
        )
    )
    wfile = io.BytesIO()
    handle_dovecot_protocol(rfile, wfile, notifier)
    assert wfile.getvalue() == b"\n"


def test_notifier_thread_firstrun(notifier, testaddr):
    reqmock = get_mocked_requests([200])
    notifier.add_token(testaddr, "01234")
    notifier.new_message_for_addr(testaddr)
    notifier.thread_retry_one(reqmock, numtries=0)
    url, data, timeout = reqmock.requests[0]
    assert data == "01234"
    assert notifier.get_tokens(testaddr) == ["01234"]


def test_notifier_thread_run(notifier, testaddr):
    notifier.add_token(testaddr, "01234")
    notifier.new_message_for_addr(testaddr)
    reqmock = get_mocked_requests([200])
    notifier.thread_retry_one(reqmock, numtries=0)
    url, data, timeout = reqmock.requests[0]
    assert data == "01234"
    assert notifier.get_tokens(testaddr) == ["01234"]


@pytest.mark.parametrize("status", [requests.exceptions.RequestException(), 404, 500])
def test_notifier_thread_connection_failures(notifier, testaddr, status, caplog):
    """ test that tokens keep getting retried until they are given up. """
    notifier.add_token(testaddr, "01234")
    notifier.new_message_for_addr(testaddr)
    notifier.NOTIFICATION_RETRY_DELAY = 5
    for i in range(notifier.MAX_NUMBER_OF_TRIES):
        caplog.clear()
        reqmock = get_mocked_requests([status])
        sleep_calls = []
        notifier.thread_retry_one(reqmock, numtries=i, sleepfunc=sleep_calls.append)
        assert notifier.retry_queues[i].qsize() == 0
        assert "request failed" in caplog.records[0].msg
        if i > 0:
            assert len(sleep_calls) == 1
        if i + 1 < notifier.MAX_NUMBER_OF_TRIES:
            assert notifier.retry_queues[i + 1].qsize() == 1
            assert len(caplog.records) == 1
        else:
            assert len(caplog.records) == 2
            assert "giving up" in caplog.records[1].msg


def test_multi_device_notifier(notifier, testaddr):
    notifier.add_token(testaddr, "01234")
    notifier.add_token(testaddr, "56789")
    notifier.new_message_for_addr(testaddr)

    reqmock = get_mocked_requests([200, 200])
    notifier.thread_retry_one(reqmock, numtries=0)
    notifier.thread_retry_one(reqmock, numtries=0)
    assert notifier.retry_queues[0].qsize() == 0
    assert notifier.retry_queues[1].qsize() == 0
    url, data, timeout = reqmock.requests[0]
    assert data == "01234"
    url, data, timeout = reqmock.requests[1]
    assert data == "56789"
    assert notifier.get_tokens(testaddr) == ["01234", "56789"]


def test_notifier_thread_run_gone_removes_token(notifier, testaddr):
    notifier.add_token(testaddr, "01234")
    notifier.add_token(testaddr, "45678")
    notifier.new_message_for_addr(testaddr)
    reqmock = get_mocked_requests([410, 200])
    notifier.thread_retry_one(reqmock, numtries=0)
    notifier.thread_retry_one(reqmock, numtries=0)
    url, data, timeout = reqmock.requests[0]
    assert data == "01234"
    url, data, timeout = reqmock.requests[1]
    assert data == "45678"
    assert notifier.get_tokens(testaddr) == ["45678"]
    assert notifier.retry_queues[0].qsize() == 0
    assert notifier.retry_queues[1].qsize() == 0
