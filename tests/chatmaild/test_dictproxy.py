import json

import pytest
import threading
import queue
import traceback

import chatmaild.dictproxy
from chatmaild.dictproxy import get_user_data, lookup_passdb, handle_dovecot_request
from chatmaild.database import Database, DBError


def test_basic(db):
    lookup_passdb(db, "link2xt@c1.testrun.org", "Pieg9aeToe3eghuthe5u")
    data = get_user_data(db, "link2xt@c1.testrun.org")
    assert data
    data2 = lookup_passdb(db, "link2xt@c1.testrun.org", "Pieg9aeToe3eghuthe5u")
    assert data == data2


def test_dont_overwrite_password_on_wrong_login(db):
    """Test that logging in with a different password doesn't create a new user"""
    res = lookup_passdb(db, "newuser1@something.org", "kajdlkajsldk12l3kj1983")
    assert res["password"]
    res2 = lookup_passdb(db, "newuser1@something.org", "kajdlqweqwe")
    # this function always returns a password hash, which is actually compared by dovecot.
    assert res["password"] == res2["password"]


def test_nocreate_file(db, monkeypatch, tmpdir):
    p = tmpdir.join("nocreate")
    p.write("")
    monkeypatch.setattr(chatmaild.dictproxy, "NOCREATE_FILE", str(p))
    lookup_passdb(db, "newuser1@something.org", "zequ0Aimuchoodaechik")
    assert not get_user_data(db, "newuser1@something.org")


def test_db_version(db):
    assert db.get_schema_version() == 1


def test_too_high_db_version(db):
    with db.write_transaction() as conn:
        conn.execute("PRAGMA user_version=%s;" % (999,))
    with pytest.raises(DBError):
        db.ensure_tables()


def test_handle_dovecot_request(db):
    msg = (
        "Lshared/passdb/laksjdlaksjdlaksjdlk12j3l1k2j3123/"
        "some42@c3.testrun.org\tsome42@c3.testrun.org"
    )
    res = handle_dovecot_request(msg, db, "c3.testrun.org")
    assert res
    assert res[0] == "O" and res.endswith("\n")
    userdata = json.loads(res[1:].strip())
    assert userdata["home"] == "/home/vmail/some42@c3.testrun.org"
    assert userdata["uid"] == userdata["gid"] == "vmail"
    assert userdata["password"].startswith("{SHA512-CRYPT}")


def test_100_concurrent_lookups(db):
    num = 100
    dbs = [Database(db.path) for i in range(num)]
    print(f"created {num} databases")
    results = queue.Queue()

    def lookup(db):
        try:
            lookup_passdb(db, "something@c1.testrun.org", "Pieg9aeToe3eghuthe5u")
        except Exception:
            results.put(traceback.format_exc())
        else:
            results.put(None)

    threads = [threading.Thread(target=lookup, args=(db,), daemon=True) for db in dbs]

    print(f"created {num} threads, starting them and waiting for results")
    for thread in threads:
        thread.start()

    for _ in dbs:
        res = results.get()
        if res is not None:
            pytest.fail(f"concurrent lookup failed\n{res}")
