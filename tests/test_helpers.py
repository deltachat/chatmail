import textwrap
import importlib.resources

from deploy_chatmail.www import build_webpages
from chatmaild.config import read_config


def create_ini(inipath, domain="example.org"):
    inipath.write_text(
        textwrap.dedent(
            f"""\
        [params]
        max_user_send_per_minute = 60
        filtermail_smtp_port = 10080
        postfix_reinject_port = 10025

        [privacy:{domain}]
        domain = example.org
        privacy_postal =
            address-line1
            address-line2

        privacy_mail = privacy@{domain}

        privacy_pdo =
            address-line3
    """
        )
    )


def test_build_webpages(tmp_path):
    pkgroot = importlib.resources.files("deploy_chatmail")
    src_dir = pkgroot.joinpath("../../../www/src").resolve()
    assert src_dir.exists(), src_dir

    inipath = tmp_path.joinpath("chatmail.ini")
    create_ini(inipath, "example.org")
    config = read_config(inipath, "example.org")
    build_dir = tmp_path.joinpath("build")
    build_webpages(src_dir, build_dir, config)


def test_get_settings(tmp_path):
    inipath = tmp_path.joinpath("chatmail.ini")
    create_ini(inipath, "example.org")

    config = read_config(inipath, "example.org")
    assert config.privacy_postal == "address-line1\naddress-line2"
    assert config.privacy_mail == "privacy@example.org"
    assert config.privacy_pdo == "address-line3"
    assert config.mailname == "example.org"
