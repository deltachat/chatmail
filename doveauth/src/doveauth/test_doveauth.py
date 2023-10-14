import subprocess
import pytest

from doveauth.doveauth import get_user_data, verify_user, Database


@pytest.fixture()
def db(tmpdir):
    return Database(tmpdir / "passdb.sqlite")


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
