import pytest

from chatctl import get_user_data, verify_user


def test_basic():
    data = get_user_data(b"link2xt@instant2.testrun.org")
    assert data


@pytest.mark.xfail(reason="no persistence yet")
def test_verify_or_create():
    res = verify_user(b"newuser1@something.org", b"kajdlkajsldk12l3kj1983")
    assert res["status"] == "ok"
    res = verify_user(b"newuser1@something.org", b"kajdlqweqwe")
    assert res["status"] == "fail"
