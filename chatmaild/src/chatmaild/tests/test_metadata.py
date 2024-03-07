from chatmaild.metadata import (
    handle_dovecot_request,
)


def test_handle_dovecot_request_happy_path():
    tokens = {}
    transactions = {}

    # lookups return the same NOTFOUND result
    res = handle_dovecot_request("Lpriv/123/chatmail", transactions, tokens, None)
    assert res == b"N\n"
    assert not tokens and not transactions

    # set device token in a transaction
    tx = "1111"
    msg = f"B{tx}\tuser"
    res = handle_dovecot_request(msg, transactions, tokens, None)
    assert not res and not tokens
    assert transactions == {tx: b"O\n"}

    msg = f"S{tx}\tpriv/guid00/devicetoken\t01234"
    res = handle_dovecot_request(msg, transactions, tokens, None)
    assert not res
    assert len(transactions) == 1
    assert len(tokens) == 1 and tokens["guid00"] == "01234"

    msg = f"C{tx}"
    res = handle_dovecot_request(msg, transactions, tokens, None)
    assert res == b"O\n"
    assert len(transactions) == 0
    assert tokens["guid00"] == "01234"

    # trigger notification for incoming message
    assert handle_dovecot_request(f"B{tx}\tuser", transactions, tokens, None) is None
    msg = f"S{tx}\tpriv/guid00/messagenew"
    requests = []
    assert handle_dovecot_request(msg, transactions, tokens, requests.append) is None
    assert requests == ["01234"]
    assert handle_dovecot_request(f"C{tx}\tuser", transactions, tokens, None) == b"O\n"
    assert not transactions
