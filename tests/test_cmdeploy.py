import pytest
from deploy_chatmail.cmdeploy import get_parser, main
from chatmaild.config import read_config


class TestCmdline:
    def test_parser(self, capsys):
        parser = get_parser()
        parser.parse_args([])
        init = parser.parse_args(["init", "chat.example.org"])
        update = parser.parse_args(["install"])
        assert init and update

    def test_init(self, tmpdir):
        tmpdir.chdir()
        main(["init", "chat.example.org"])
        inipath = tmpdir.join("chatmail.ini")
        config = read_config(inipath.strpath)
        assert config.mailname == "chat.example.org"

    def test_init_not_overwrite(self, tmpdir):
        tmpdir.chdir()
        main(["init", "chat.example.org"])
        with pytest.raises(SystemExit):
            main(["init", "chat.example.org"])
