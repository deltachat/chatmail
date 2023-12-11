import os

import pytest
from deploy_chatmail.cmdeploy import get_parser, main
from chatmaild.config import read_config


@pytest.fixture(autouse=True)
def _chdir(tmp_path):
    old = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(old)


class TestCmdline:
    def test_parser(self, capsys):
        parser = get_parser()
        parser.parse_args([])
        init = parser.parse_args(["init", "chat.example.org"])
        run = parser.parse_args(["run"])
        assert init and run

    def test_init(self, tmp_path):
        main(["init", "chat.example.org"])
        inipath = tmp_path.joinpath("chatmail.ini")
        config = read_config(inipath)
        assert config.mail_domain == "chat.example.org"

    def test_init_not_overwrite(self):
        main(["init", "chat.example.org"])
        with pytest.raises(SystemExit):
            main(["init", "chat.example.org"])
