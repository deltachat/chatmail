import os

import pytest

import chatmaild.dictproxy
from chatmaild.dictproxy import DictProxy
from chatmaild.database import DBError


@pytest.fixture
def dictproxy(db, maildomain):
    return DictProxy(db, maildomain)


def test_basic(dictproxy, tmpdir, monkeypatch):
    monkeypatch.setattr(
        chatmaild.dictproxy, "NOCREATE_FILE", tmpdir.join("nocreate").strpath
    )
    dictproxy.lookup_passdb("link2xt@c1.testrun.org", "asdf")
    assert dictproxy.get_user_data("link2xt@c1.testrun.org")


def test_dont_overwrite_password_on_wrong_login(dictproxy):
    """Test that logging in with a different password doesn't create a new user"""
    res = dictproxy.lookup_passdb("newuser1@something.org", "kajdlkajsldk12l3kj1983")
    assert res["password"]
    res2 = dictproxy.lookup_passdb("newuser1@something.org", "kajdlqweqwe")
    # this function always returns a password hash, which is actually compared by dovecot.
    assert res["password"] == res2["password"]


def test_nocreate_file(dictproxy, tmpdir, monkeypatch):
    nocreate = tmpdir.join("nocreate")
    monkeypatch.setattr(chatmaild.dictproxy, "NOCREATE_FILE", str(nocreate))
    nocreate.write("")
    dictproxy.lookup_passdb("newuser1@something.org", "kajdlqweqwe")
    assert not dictproxy.get_user_data("newuser1@something.org")


def test_db_version(db):
    assert db.get_schema_version() == 1


def test_too_high_db_version(db):
    with db.write_transaction() as conn:
        conn.execute("PRAGMA user_version=%s;" % (999,))
    with pytest.raises(DBError):
        db.ensure_tables()
