import io
import json
import pytest
import queue
import threading
import traceback

import chatmaild.doveauth
from chatmaild.doveauth import (
    get_user_data,
    lookup_passdb,
    handle_dovecot_request,
    handle_dovecot_protocol,
)
from chatmaild.database import DBError


def test_basic(db, example_config):
    lookup_passdb(db, example_config, "asdf12345@chat.example.org", "q9mr3faue")
    data = get_user_data(db, example_config, "asdf12345@chat.example.org")
    assert data
    data2 = lookup_passdb(
        db, example_config, "asdf12345@chat.example.org", "q9mr3jewvadsfaue"
    )
    assert data == data2


def test_dont_overwrite_password_on_wrong_login(db, example_config):
    """Test that logging in with a different password doesn't create a new user"""
    res = lookup_passdb(
        db, example_config, "newuser12@chat.example.org", "kajdlkajsldk12l3kj1983"
    )
    assert res["password"]
    res2 = lookup_passdb(db, example_config, "newuser12@chat.example.org", "kajdslqwe")
    # this function always returns a password hash, which is actually compared by dovecot.
    assert res["password"] == res2["password"]


def test_nocreate_file(db, monkeypatch, tmpdir, example_config):
    p = tmpdir.join("nocreate")
    p.write("")
    monkeypatch.setattr(chatmaild.doveauth, "NOCREATE_FILE", str(p))
    lookup_passdb(
        db, example_config, "newuser12@chat.example.org", "zequ0Aimuchoodaechik"
    )
    assert not get_user_data(db, example_config, "newuser12@chat.example.org")


def test_db_version(db):
    assert db.get_schema_version() == 1


def test_too_high_db_version(db):
    with db.write_transaction() as conn:
        conn.execute("PRAGMA user_version=%s;" % (999,))
    with pytest.raises(DBError):
        db.ensure_tables()


def test_handle_dovecot_request(db, example_config):
    # Test that password can contain ", ', \ and /
    msg = (
        'Lshared/passdb/laksjdlaksjdlak\\\\sjdlk\\"12j\\\'3l1/k2j3123"'
        "some42123@chat.example.org\tsome42123@chat.example.org"
    )
    res = handle_dovecot_request(msg, db, example_config)
    assert res
    assert res[0] == "O" and res.endswith("\n")
    userdata = json.loads(res[1:].strip())
    assert (
        userdata["home"]
        == "/home/vmail/mail/chat.example.org/some42123@chat.example.org"
    )
    assert userdata["uid"] == userdata["gid"] == "vmail"
    assert userdata["password"].startswith("{SHA512-CRYPT}")


def test_handle_dovecot_protocol(db, example_config):
    rfile = io.BytesIO(
        b"H3\t2\t0\t\tauth\nLshared/userdb/foobar@chat.example.org\tfoobar@chat.example.org\n"
    )
    wfile = io.BytesIO()
    handle_dovecot_protocol(rfile, wfile, db, example_config)
    assert wfile.getvalue() == b"N\n"


def test_50_concurrent_lookups_different_accounts(db, gencreds, example_config):
    num_threads = 50
    req_per_thread = 5
    results = queue.Queue()

    def lookup(db):
        for i in range(req_per_thread):
            addr, password = gencreds()
            try:
                lookup_passdb(db, example_config, addr, password)
            except Exception:
                results.put(traceback.format_exc())
            else:
                results.put(None)

    threads = []
    for i in range(num_threads):
        thread = threading.Thread(target=lookup, args=(db,), daemon=True)
        threads.append(thread)

    print(f"created {num_threads} threads, starting them and waiting for results")
    for thread in threads:
        thread.start()

    for i in range(num_threads * req_per_thread):
        res = results.get()
        if res is not None:
            pytest.fail(f"concurrent lookup failed\n{res}")
