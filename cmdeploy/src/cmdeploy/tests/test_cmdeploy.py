import os

import pytest
from cmdeploy.cmdeploy import get_parser, main


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

    @pytest.mark.xfail(reason="init doesn't exit anymore, check for CLI output instead")
    def test_init_not_overwrite(self):
        main(["init", "chat.example.org"])
        with pytest.raises(SystemExit):
            main(["init", "chat.example.org"])
