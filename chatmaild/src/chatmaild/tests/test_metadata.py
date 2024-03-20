import io
import pytest

from chatmaild.metadata import (
    handle_dovecot_request,
    handle_dovecot_protocol,
    Notifier,
)


@pytest.fixture
def notifier(tmp_path):
    metadata_dir = tmp_path.joinpath("metadata")
    if not metadata_dir.exists():
        metadata_dir.mkdir()
    return Notifier(metadata_dir)


def test_notifier_persistence(tmp_path):
    metadata_dir = tmp_path.joinpath("metadata")
    metadata_dir.mkdir()
    notifier1 = Notifier(metadata_dir)
    notifier2 = Notifier(metadata_dir)
    assert notifier1.get_token(guid="guid00") is None
    assert notifier2.get_token(guid="guid00") is None

    notifier1.set_token("guid00", "01234")
    notifier1.set_token("guid03", "456")
    assert notifier2.get_token("guid00") == "01234"
    assert notifier2.get_token("guid03") == "456"
    notifier2.del_token("guid00")
    assert notifier1.get_token("guid00") is None


def test_handle_dovecot_request_lookup_fails(notifier):
    res = handle_dovecot_request("Lpriv/123/chatmail", {}, notifier)
    assert res == "N\n"


def test_handle_dovecot_request_happy_path(notifier):
    transactions = {}

    # lookups return the same NOTFOUND result
    res = handle_dovecot_request("Lpriv/123/chatmail", transactions, notifier)
    assert res == "N\n"
    assert notifier.get_token("guid00") is None and not transactions

    # set device token in a transaction
    tx = "1111"
    msg = f"B{tx}\tuser"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert not res and notifier.get_token("guid00") is None
    assert transactions == {tx: "O\n"}

    msg = f"S{tx}\tpriv/guid00/devicetoken\t01234"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert not res
    assert len(transactions) == 1
    assert notifier.get_token("guid00") == "01234"

    msg = f"C{tx}"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert res == "O\n"
    assert len(transactions) == 0
    assert notifier.get_token("guid00") == "01234"

    # trigger notification for incoming message
    assert handle_dovecot_request(f"B{tx}\tuser", transactions, notifier) is None
    msg = f"S{tx}\tpriv/guid00/messagenew"
    assert handle_dovecot_request(msg, transactions, notifier) is None
    assert notifier.to_notify_queue.get() == "guid00"
    assert notifier.to_notify_queue.qsize() == 0
    assert handle_dovecot_request(f"C{tx}\tuser", transactions, notifier) == "O\n"
    assert not transactions


def test_handle_dovecot_protocol_set_devicetoken(notifier):
    rfile = io.BytesIO(
        b"\n".join(
            [
                b"HELLO",
                b"Btx00\tuser",
                b"Stx00\tpriv/guid00/devicetoken\t01234",
                b"Ctx00",
            ]
        )
    )
    wfile = io.BytesIO()
    handle_dovecot_protocol(rfile, wfile, notifier)
    assert notifier.get_token("guid00") == "01234"
    assert wfile.getvalue() == b"O\n"


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
                b"Btx01\tuser",
                b"Stx01\tpriv/guid00/messagenew",
                b"Ctx01",
            ]
        )
    )
    wfile = io.BytesIO()
    handle_dovecot_protocol(rfile, wfile, notifier)
    assert wfile.getvalue() == b"O\n"
    assert notifier.to_notify_queue.get() == "guid00"
    assert notifier.to_notify_queue.qsize() == 0


def test_notifier_thread_run(notifier):
    requests = []

    class ReqMock:
        def post(self, url, data, timeout):
            requests.append((url, data, timeout))

            class Result:
                status_code = 200

            return Result()

    notifier.set_token("guid00", "01234")
    notifier.new_message_for_guid("guid00")
    notifier.thread_run_one(ReqMock())
    url, data, timeout = requests[0]
    assert data == "01234"
    assert notifier.get_token("guid00") == "01234"


def test_notifier_thread_run_gone_removes_token(notifier):
    requests = []

    class ReqMock:
        def post(self, url, data, timeout):
            requests.append((url, data, timeout))

            class Result:
                status_code = 410

            return Result()

    notifier.set_token("guid00", "01234")
    notifier.new_message_for_guid("guid00")
    assert notifier.get_token("guid00") == "01234"
    notifier.thread_run_one(ReqMock())
    url, data, timeout = requests[0]
    assert data == "01234"
    assert notifier.get_token("guid00") is None
