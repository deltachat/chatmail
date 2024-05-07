import importlib.resources
import os

import pyinfra

from cmdeploy import deploy_chatmail


def main():
    config_path = os.getenv(
        "CHATMAIL_INI",
        importlib.resources.files("cmdeploy").joinpath("../../../chatmail.ini"),
    )

    deploy_chatmail(config_path)


if pyinfra.is_cli:
    main()
