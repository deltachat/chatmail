from chatmaild.config import read_config


def test_read_config_basic(example_config):
    assert example_config.mail_domain == "chat.example.org"
    assert not example_config.privacy_supervisor and not example_config.privacy_mail
    assert not example_config.privacy_pdo and not example_config.privacy_postal

    inipath = example_config._inipath
    inipath.write_text(inipath.read_text().replace("60", "37"))
    example_config = read_config(inipath)
    assert example_config.max_user_send_per_minute == 37
    assert example_config.mail_domain == "chat.example.org"


def test_read_config_testrun(make_config):
    config = make_config("something.testrun.org")
    assert config.mail_domain == "something.testrun.org"
    assert len(config.privacy_postal.split("\n")) > 1
    assert len(config.privacy_supervisor.split("\n")) > 1
    assert len(config.privacy_pdo.split("\n")) > 1
    assert config.privacy_mail == "privacy@testrun.org"
    assert config.filtermail_smtp_port == 10080
    assert config.postfix_reinject_port == 10025
    assert config.max_user_send_per_minute == 60
    assert config.max_mailbox_size == "100M"
    assert config.delete_mails_after == "40"
    assert config.username_min_length == 9
    assert config.username_max_length == 9
    assert config.password_min_length == 9
    assert config.passthrough_recipients == ["privacy@testrun.org"]
    assert config.passthrough_senders == []
