import io

from chatmaild.metadata import (
    handle_dovecot_request,
    handle_dovecot_protocol,
    Notifier,
)


def test_handle_dovecot_request_lookup_fails():
    notifier = Notifier()
    res = handle_dovecot_request("Lpriv/123/chatmail", {}, notifier)
    assert res == "N\n"


def test_handle_dovecot_request_happy_path():
    notifier = Notifier()
    transactions = {}

    # lookups return the same NOTFOUND result
    res = handle_dovecot_request("Lpriv/123/chatmail", transactions, notifier)
    assert res == "N\n"
    assert not notifier.guid2token and not transactions

    # set device token in a transaction
    tx = "1111"
    msg = f"B{tx}\tuser"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert not res and not notifier.guid2token
    assert transactions == {tx: "O\n"}

    msg = f"S{tx}\tpriv/guid00/devicetoken\t01234"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert not res
    assert len(transactions) == 1
    assert len(notifier.guid2token) == 1
    assert notifier.guid2token["guid00"] == "01234"

    msg = f"C{tx}"
    res = handle_dovecot_request(msg, transactions, notifier)
    assert res == "O\n"
    assert len(transactions) == 0
    assert notifier.guid2token["guid00"] == "01234"

    # trigger notification for incoming message
    assert handle_dovecot_request(f"B{tx}\tuser", transactions, notifier) is None
    msg = f"S{tx}\tpriv/guid00/messagenew"
    assert handle_dovecot_request(msg, transactions, notifier) is None
    assert notifier.to_notify_queue.get() == "guid00"
    assert notifier.to_notify_queue.qsize() == 0
    assert handle_dovecot_request(f"C{tx}\tuser", transactions, notifier) == "O\n"
    assert not transactions


def test_handle_dovecot_protocol_set_devicetoken():
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
    notifier = Notifier()
    handle_dovecot_protocol(rfile, wfile, notifier)
    assert notifier.guid2token["guid00"] == "01234"
    assert wfile.getvalue() == b"O\n"


def test_handle_dovecot_protocol_messagenew():
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
    notifier = Notifier()
    handle_dovecot_protocol(rfile, wfile, notifier)
    assert wfile.getvalue() == b"O\n"
    assert notifier.to_notify_queue.get() == "guid00"
    assert notifier.to_notify_queue.qsize() == 0


def test_notifier_thread_run():
    requests = []

    class ReqMock:
        def post(self, url, data, timeout):
            requests.append((url, data, timeout))

            class Result:
                status_code = 200

            return Result()

    notifier = Notifier()
    notifier.set_token("guid00", "01234")
    notifier.new_message_for_guid("guid00")
    notifier.thread_run_one(ReqMock())
    url, data, timeout = requests[0]
    assert data == "01234"
    assert len(notifier.guid2token) == 1


def test_notifier_thread_run_gone_removes_token():
    requests = []

    class ReqMock:
        def post(self, url, data, timeout):
            requests.append((url, data, timeout))

            class Result:
                status_code = 410

            return Result()

    notifier = Notifier()
    notifier.set_token("guid00", "01234")
    notifier.new_message_for_guid("guid00")
    assert notifier.guid2token["guid00"] == "01234"
    notifier.thread_run_one(ReqMock())
    url, data, timeout = requests[0]
    assert data == "01234"
    assert len(notifier.guid2token) == 0
