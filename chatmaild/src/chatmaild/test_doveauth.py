import os

import pytest

from .dictproxy import get_user_data, lookup_passdb
from .database import Database, DBError


@pytest.fixture()
def db(tmpdir):
    db_path = tmpdir / "passdb.sqlite"
    print("database path:", db_path)
    return Database(db_path)


def test_basic(db):
    if os.path.exists("/tmp/nocreate"):
        os.remove("/tmp/nocreate")
    lookup_passdb(db, "link2xt@c1.testrun.org", "asdf")
    data = get_user_data(db, "link2xt@c1.testrun.org")
    assert data


def test_dont_overwrite_password_on_wrong_login(db):
    """Test that logging in with a different password doesn't create a new user"""
    res = lookup_passdb(db, "newuser1@something.org", "kajdlkajsldk12l3kj1983")
    assert res["password"]
    res2 = lookup_passdb(db, "newuser1@something.org", "kajdlqweqwe")
    # this function always returns a password hash, which is actually compared by dovecot.
    assert res["password"] == res2["password"]


def test_nocreate_file(db):
    with open("/tmp/nocreate", "w+") as f:
        f.write("")
    assert os.path.exists("/tmp/nocreate")
    lookup_passdb(db, "newuser1@something.org", "kajdlqweqwe")
    assert not get_user_data(db, "newuser1@something.org")
    os.remove("/tmp/nocreate")


def test_db_version(db):
    assert db.get_schema_version() == 1


def test_too_high_db_version(db):
    with db.write_transaction() as conn:
        conn.execute("PRAGMA user_version=%s;" % (999,))
    with pytest.raises(DBError):
        db.ensure_tables()
