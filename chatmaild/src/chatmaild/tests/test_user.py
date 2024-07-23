def test_login_timestamp(testaddr, example_config):
    user = example_config.get_user(testaddr)
    user.set_password("someeqkjwelkqwjleqwe")
    user.set_last_login_timestamp(100000)
    assert user.get_last_login_timestamp() == 86400

    user.set_last_login_timestamp(200000)
    assert user.get_last_login_timestamp() == 86400 * 2


def test_get_user_dict_not_set(testaddr, example_config, caplog):
    user = example_config.get_user(testaddr)
    assert not caplog.records
    assert user.get_userdb_dict() == {}
    assert len(caplog.records) == 1

    user.set_password("")
    assert user.get_userdb_dict() == {}
    assert len(caplog.records) == 2


def test_get_user_dict(make_config, tmp_path):
    config = make_config("something.testrun.org")
    addr = "user1@something.org"
    user = config.get_user(addr)
    enc_password = "l1k2j31lk2j3l1k23j123"
    user.set_password(enc_password)
    data = user.get_userdb_dict()
    assert addr in str(data["home"])
    assert data["uid"] == "vmail"
    assert data["gid"] == "vmail"
    assert data["password"] == enc_password
