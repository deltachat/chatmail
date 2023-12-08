from chatmaild.config import read_config


def test_read_config_no_privacy_policy(tmp_path, create_ini):
    inipath = create_ini(
        """
        [privacy:testrun]
        domain = *.example.org
    """
    )
    config = read_config(inipath, "something.example.org")
    assert config.mailname == "something.example.org"
    assert not config.has_privacy_policy


def test_read_config(create_ini):
    inipath = create_ini(
        """
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
    assert config.has_privacy_policy

    assert config.mailname == "something.testrun.org"
    assert config.privacy_postal == "Postal Ltd"
    assert config.privacy_mail == "privacy@merlinux.eu"
    lines = config.privacy_pdo.split("\n")
    assert lines[0] == "Postal PDO"
    assert lines[1].startswith("You can ")
    lines = config.privacy_supervisor.split("\n")
    assert lines[0] == "line1"
    assert lines[1] == "line2 with space"
