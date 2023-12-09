from chatmaild.config import read_config
import chatmaild.config


def test_read_config_without_mailname(tmp_path, create_ini, monkeypatch):
    mailname_path = tmp_path.joinpath("mailname")
    mailname_path.write_text("something.example.org")
    monkeypatch.setattr(chatmaild.config, "system_mailname_path", mailname_path)

    inipath = create_ini(
        """
        [params]
        max_user_send_per_minute = 40
        filtermail_smtp_port = 9875
        postfix_reinject_port = 9999
        passthrough_recipients =
    """
    )
    config = read_config(inipath)
    assert config.mailname == "something.example.org"


def test_read_config_without_privacy_policy(tmp_path, create_ini):
    inipath = create_ini(
        """
        [params]
        max_user_send_per_minute = 40
        filtermail_smtp_port = 9875
        postfix_reinject_port = 9999
        passthrough_recipients =

        [privacy:testrun]
        domain = *.example.org
    """
    )
    config = read_config(inipath, "something.example.org")
    assert config.mailname == "something.example.org"
    assert config.max_user_send_per_minute == 40
    assert config.filtermail_smtp_port == 9875
    assert config.postfix_reinject_port == 9999
    assert config.passthrough_recipients == []
    assert not config.privacy_postal
    assert not config.privacy_mail
    assert not config.privacy_pdo
    assert not config.privacy_supervisor


def test_read_config(create_ini):
    inipath = create_ini(
        """
        [params]
        max_user_send_per_minute = 40
        filtermail_smtp_port = 10080
        postfix_reinject_port = 10025
        passthrough_recipients = x@example.org y@example.org

        [privacy:testrun]
        domain = *.testrun.org

        privacy_postal =
            Postal Ltd

        privacy_mail = privacy@merlinux.eu

        privacy_pdo =
            Postal PDO
            You can contact him at *delta-privacy@merlinux.eu* (Keyword: DPO)

        privacy_supervisor =
            line1
            line2 with space
    """
    )

    config = read_config(inipath, "something.testrun.org")

    assert config.mailname == "something.testrun.org"
    assert config.filtermail_smtp_port == 10080
    assert config.postfix_reinject_port == 10025
    assert config.passthrough_recipients == ["x@example.org", "y@example.org"]
    assert config.privacy_postal == "Postal Ltd"
    assert config.privacy_mail == "privacy@merlinux.eu"
    lines = config.privacy_pdo.split("\n")
    assert lines[0] == "Postal PDO"
    assert lines[1].startswith("You can ")
    lines = config.privacy_supervisor.split("\n")
    assert lines[0] == "line1"
    assert lines[1] == "line2 with space"
