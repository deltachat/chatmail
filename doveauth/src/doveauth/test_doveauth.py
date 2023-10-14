import subprocess
import pytest

from doveauth import get_user_data, verify_user, Database, DBError


@pytest.fixture()
def db(tmpdir):
    db_path = tmpdir / "passdb.sqlite"
    print("database path:", db_path)
    return Database(db_path)


def test_basic(db):
    verify_user(db, "link2xt@c1.testrun.org", "asdf")
    data = get_user_data(db, "link2xt@c1.testrun.org")
    assert data


def test_verify_or_create(db):
    res = verify_user(db, "newuser1@something.org", "kajdlkajsldk12l3kj1983")
    assert res["status"] == "ok"
    res = verify_user(db, "newuser1@something.org", "kajdlqweqwe")
    assert res["status"] == "fail"


def test_lua_integration(request):
    p = request.fspath.dirpath("test_doveauth.lua")
    proc = subprocess.run(["lua", str(p)])
    assert proc.returncode == 0


def test_db_version(db):
    assert db.get_schema_version() == 1


def test_too_high_db_version(db):
    with db.write_transaction() as conn:
        conn.execute("PRAGMA user_version=%s;" % (999,))
    with pytest.raises(DBError):
        db.ensure_tables()
