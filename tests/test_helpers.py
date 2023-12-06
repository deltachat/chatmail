import textwrap

from deploy_chatmail import make_privacy_html_j2, get_ini_settings


def test_privacy(tmp_path):
    path = tmp_path.joinpath("privacy.md")
    path.write_text("# privacy policy")
    output = make_privacy_html_j2(path)
    assert output.exists()
    print(output.read_text())


def test_get_settings(tmp_path):
    inipath = tmp_path.joinpath("chatmail.ini")
    inipath.write_text(
        textwrap.dedent(
            """\
        [config]

        privacy_postal =
            address-line1
            address-line2

        privacy_mail = privacy@example.org

        privacy_pdo =
            address-line3
    """
        )
    )
    d = get_ini_settings("x.testrun.org", inipath)
    assert d["privacy_postal"] == "address-line1\naddress-line2"
    assert d["privacy_mail"] == "privacy@example.org"
    assert d["privacy_pdo"] == "address-line3"
    assert d["mail_domain"] == "x.testrun.org"