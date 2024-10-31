import importlib.resources
import os

import pyinfra

from cmdeploy import deploy_chatmail


def main():
    config_path = os.getenv(
        "CHATMAIL_INI",
        importlib.resources.files("cmdeploy").joinpath("../../../chatmail.ini"),
    )
    disable_mail = bool(os.environ.get('CHATMAIL_DISABLE_MAIL'))
    require_iroh = bool(os.environ.get('CHATMAIL_REQUIRE_IROH'))

    deploy_chatmail(config_path, disable_mail, require_iroh)


if pyinfra.is_cli:
    main()
