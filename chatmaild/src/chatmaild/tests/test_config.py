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


def test_read_config_testrun(example_config):
    assert example_config.mail_domain == "something.testrun.org"
    assert len(example_config.privacy_postal.split("\n")) > 1
    assert len(example_config.privacy_supervisor.split("\n")) > 1
    assert len(example_config.privacy_pdo.split("\n")) > 1
    assert example_config.privacy_mail == "privacy@testrun.org"
    assert example_config.filtermail_smtp_port == 10080
    assert example_config.postfix_reinject_port == 10025
    assert example_config.max_user_send_per_minute == 60
    assert example_config.max_mailbox_size == "100M"
    assert example_config.delete_mails_after == "40d"
    assert example_config.username_min_length == 6
    assert example_config.username_max_length == 20
    assert example_config.password_min_length == 9
    assert example_config.passthrough_senders
    assert example_config.passthrough_recipients
