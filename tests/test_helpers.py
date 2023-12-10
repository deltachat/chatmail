import importlib.resources

from deploy_chatmail.www import build_webpages


def test_build_webpages(tmp_path, make_config):
    pkgroot = importlib.resources.files("deploy_chatmail")
    src_dir = pkgroot.joinpath("../../../www/src").resolve()
    assert src_dir.exists(), src_dir
    config = make_config("chat.example.org")
    build_dir = tmp_path.joinpath("build")
    build_webpages(src_dir, build_dir, config)
    assert len([x for x in build_dir.iterdir() if x.suffix == ".html"]) >= 3
