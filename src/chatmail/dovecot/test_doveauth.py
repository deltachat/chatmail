import subprocess
import pytest

from doveauth import get_user_data, verify_user


def test_basic():
    data = get_user_data("link2xt@c1.testrun.org")
    assert data


@pytest.mark.xfail(reason="no persistence yet")
def test_verify_or_create():
    res = verify_user("newuser1@something.org", "kajdlkajsldk12l3kj1983")
    assert res["status"] == "ok"
    res = verify_user("newuser1@something.org", "kajdlqweqwe")
    assert res["status"] == "fail"


def test_lua_integration(request):
    p = request.fspath.dirpath("test_doveauth.lua")
    proc = subprocess.run(["lua", str(p)])
    assert proc.returncode == 0
