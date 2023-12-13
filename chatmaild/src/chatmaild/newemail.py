#!/usr/local/lib/chatmaild/venv/bin/python3

""" CGI script for creating new accounts. """

import json
import random

from chatmaild.config import read_config, Config

CONFIG_PATH = "/usr/local/lib/chatmaild/chatmail.ini"
ALPHANUMERIC = "abcdefghijklmnopqrstuvwxyz1234567890"
ALPHANUMERIC_PUNCT = r"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890!#$%&'()*+,-./:;<=>?@[\]^_`{|}~." + r'"'


def create_newemail_dict(config: Config):
    user = "".join(random.choices(ALPHANUMERIC, k=config.username_min_length))
    password = "".join(random.choices(ALPHANUMERIC_PUNCT, k=config.password_min_length + 3))
    return dict(email=f"{user}@{config.mail_domain}", password=f"{password}")


def print_new_account():
    config = read_config(CONFIG_PATH)
    creds = create_newemail_dict(config)

    print("Content-Type: application/json")
    print("")
    print(json.dumps(creds))


if __name__ == "__main__":
    print_new_account()
