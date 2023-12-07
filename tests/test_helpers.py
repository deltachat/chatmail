import textwrap
import importlib.resources

from deploy_chatmail.www import build_webpages
from deploy_chatmail import get_ini_settings

def create_ini(inipath):
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

def test_build_webpages(tmp_path):
    pkgroot = importlib.resources.files("deploy_chatmail")
    src_dir = pkgroot.joinpath("../../../www/src").resolve()
    assert src_dir.exists(), src_dir

    inipath = tmp_path.joinpath("chatmail.ini")
    create_ini(inipath)
    config = get_ini_settings("example.org", inipath)
    build_dir = tmp_path.joinpath("build")
    build_webpages(src_dir, build_dir, config)


def test_get_settings(tmp_path):
    inipath = tmp_path.joinpath("chatmail.ini")
    create_ini(inipath)

    d = get_ini_settings("x.testrun.org", inipath)
    assert d["privacy_postal"] == "address-line1\naddress-line2"
    assert d["privacy_mail"] == "privacy@example.org"
    assert d["privacy_pdo"] == "address-line3"
    assert d["mail_domain"] == "x.testrun.org"
