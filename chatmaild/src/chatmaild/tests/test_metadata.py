import io
import pytest

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


def test_handle_dovecot_request_happy_path(notifier, testaddr):
    transactions = {}

    # set device token in a transaction
    tx = "1111"
    msg = f"B{tx}\t{testaddr}"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert not res and not notifier.get_tokens(testaddr)
    assert transactions == {tx: dict(addr=testaddr, res="O\n")}

    msg = f"S{tx}\tpriv/guid00/devicetoken\t01234"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert not res
    assert len(transactions) == 1
    assert notifier.get_tokens(testaddr) == ["01234"]

    msg = f"C{tx}"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert res == "O\n"
    assert len(transactions) == 0
    assert notifier.get_tokens(testaddr) == ["01234"]

    # trigger notification for incoming message
    tx2 = "2222"
    assert handle_dovecot_request(f"B{tx2}\t{testaddr}", transactions, notifier) is None
    msg = f"S{tx2}\tpriv/guid00/messagenew"
    assert handle_dovecot_request(msg, transactions, notifier) is None
    assert notifier.notification_queue.get() == testaddr
    assert handle_dovecot_request(f"C{tx2}", transactions, notifier) == "O\n"
    assert not transactions
    assert notifier.notification_dir.joinpath(testaddr).exists()


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


def test_handle_dovecot_protocol_messagenew(notifier):
    rfile = io.BytesIO(
        b"\n".join(
            [
                b"HELLO",
                b"Btx01\tuser@example.org",
                b"Stx01\tpriv/guid00/messagenew",
                b"Ctx01",
            ]
        )
    )
    wfile = io.BytesIO()
    handle_dovecot_protocol(rfile, wfile, notifier)
    assert wfile.getvalue() == b"O\n"
    addr = notifier.notification_queue.get()
    assert notifier.notification_dir.joinpath(addr).exists()


def test_notifier_thread_run(notifier, testaddr):
    requests = []

    class ReqMock:
        def post(self, url, data, timeout):
            requests.append((url, data, timeout))

            class Result:
                status_code = 200

            return Result()

    notifier.add_token(testaddr, "01234")
    notifier.new_message_for_addr(testaddr)
    notifier.thread_run_one(ReqMock())
    url, data, timeout = requests[0]
    assert data == "01234"
    assert notifier.get_tokens(testaddr) == ["01234"]


def test_multi_device_notifier(notifier, testaddr):
    requests = []

    class ReqMock:
        def post(self, url, data, timeout):
            requests.append((url, data, timeout))

            class Result:
                status_code = 200

            return Result()

    notifier.add_token(testaddr, "01234")
    notifier.add_token(testaddr, "56789")
    notifier.new_message_for_addr(testaddr)
    notifier.thread_run_one(ReqMock())
    url, data, timeout = requests[0]
    assert data == "01234"
    url, data, timeout = requests[1]
    assert data == "56789"
    assert notifier.get_tokens(testaddr) == ["01234", "56789"]


def test_notifier_thread_run_gone_removes_token(notifier, testaddr):
    requests = []

    class ReqMock:
        def post(self, url, data, timeout):
            requests.append((url, data, timeout))

            class Result:
                status_code = 410 if data == "01234" else 200

            return Result()

    notifier.add_token(testaddr, "01234")
    notifier.new_message_for_addr(testaddr)
    assert notifier.get_tokens(testaddr) == ["01234"]
    notifier.add_token(testaddr, "45678")
    notifier.thread_run_one(ReqMock())
    url, data, timeout = requests[0]
    assert data == "01234"
    url, data, timeout = requests[1]
    assert data == "45678"
    assert notifier.get_tokens(testaddr) == ["45678"]
