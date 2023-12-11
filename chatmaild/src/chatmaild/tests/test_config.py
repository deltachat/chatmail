from chatmaild.config import read_config


def test_read_config_basic(make_config):
    config = make_config("chat.example.org")
    assert config.mailname == "chat.example.org"
    assert not config.privacy_supervisor and not config.privacy_mail
    assert not config.privacy_pdo and not config.privacy_postal

    inipath = config._inipath
    inipath.write_text(inipath.read_text().replace("60", "37"))
    config = read_config(inipath)
    assert config.max_user_send_per_minute == 37
    assert config.mailname == "chat.example.org"


def test_read_config_testrun(make_config):
    config = make_config("something.testrun.org")
    assert config.mailname == "something.testrun.org"
    assert len(config.privacy_postal.split("\n")) > 1
    assert len(config.privacy_supervisor.split("\n")) > 1
    assert len(config.privacy_pdo.split("\n")) > 1
    assert config.privacy_mail == "privacy@testrun.org"
    assert config.filtermail_smtp_port == 10080
    assert config.postfix_reinject_port == 10025
    assert config.max_user_send_per_minute == 60
    assert config.passthrough_recipients
