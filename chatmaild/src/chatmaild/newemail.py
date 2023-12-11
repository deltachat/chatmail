#!/usr/bin/python3

""" CGI script for creating new accounts. """

import json
import random

mail_domain_path = "/etc/mailname"


def create_newemail_dict(domain):
    alphanumeric = "abcdefghijklmnopqrstuvwxyz1234567890"
    user = "".join(random.choices(alphanumeric, k=9))
    password = "".join(random.choices(alphanumeric, k=12))
    return dict(email=f"{user}@{domain}", password=f"{password}")


def print_new_account():
    domain = open(mail_domain_path).read().strip()
    creds = create_newemail_dict(domain=domain)

    print("Content-Type: application/json")
    print("")
    print(json.dumps(creds))


if __name__ == "__main__":
    print_new_account()
