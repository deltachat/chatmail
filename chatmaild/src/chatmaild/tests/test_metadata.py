import io

from chatmaild.metadata import (
    handle_dovecot_request,
    handle_dovecot_protocol,
)


def test_handle_dovecot_request_lookup_fails():
    res = handle_dovecot_request("Lpriv/123/chatmail", {}, {}, None)
    assert res == "N\n"


def test_handle_dovecot_request_happy_path():
    tokens = {}
    transactions = {}

    # lookups return the same NOTFOUND result
    res = handle_dovecot_request("Lpriv/123/chatmail", transactions, tokens, None)
    assert res == "N\n"
    assert not tokens and not transactions

    # set device token in a transaction
    tx = "1111"
    msg = f"B{tx}\tuser"
    res = handle_dovecot_request(msg, transactions, tokens, None)
    assert not res and not tokens
    assert transactions == {tx: "O\n"}

    msg = f"S{tx}\tpriv/guid00/devicetoken\t01234"
    res = handle_dovecot_request(msg, transactions, tokens, None)
    assert not res
    assert len(transactions) == 1
    assert len(tokens) == 1 and tokens["guid00"] == "01234"

    msg = f"C{tx}"
    res = handle_dovecot_request(msg, transactions, tokens, None)
    assert res == "O\n"
    assert len(transactions) == 0
    assert tokens["guid00"] == "01234"

    # trigger notification for incoming message
    assert handle_dovecot_request(f"B{tx}\tuser", transactions, tokens, None) is None
    msg = f"S{tx}\tpriv/guid00/messagenew"
    requests = []
    assert handle_dovecot_request(msg, transactions, tokens, requests.append) is None
    assert requests == ["guid00"]
    assert handle_dovecot_request(f"C{tx}\tuser", transactions, tokens, None) == "O\n"
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
    tokens = {}
    wfile = io.BytesIO()
    handle_dovecot_protocol(rfile, wfile, tokens, None)
    assert tokens["guid00"] == "01234"
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
    tokens = {"guid00": "01234"}
    wfile = io.BytesIO()
    requests = []
    handle_dovecot_protocol(rfile, wfile, tokens, requests.append)
    assert wfile.getvalue() == b"O\n"
    assert requests == ["guid00"]
