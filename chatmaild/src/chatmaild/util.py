import base64
import random
import logging
import os
import crypt


NOCREATE_FILE = "/etc/chatmail-nocreate"


def is_allowed_to_create(user, cleartext_password) -> bool:
    """Return True if user and password are admissable."""
    if os.path.exists(NOCREATE_FILE):
        logging.warning(f"blocked account creation because {NOCREATE_FILE!r} exists.")
        return False

    if len(cleartext_password) < 10:
        logging.warning("Password needs to be at least 10 characters long")
        return False

    parts = user.split("@")
    if len(parts) != 2:
        logging.warning(f"user {user!r} is not a proper e-mail address")
        return False
    localpart, domain = parts

    if domain == "nine.testrun.org":
        # nine.testrun.org policy, username has to be exactly nine chars
        if len(localpart) != 9:
            logging.warning(f"localpart {localpart!r} has not exactly nine chars")
            return False

    return True


def gen_password():
    with open("/dev/urandom", "rb") as f:
        s = f.read(21)
    return base64.b64encode(s).decode("ascii")[:12]


def encrypt_password(password: str):
    # https://doc.dovecot.org/configuration_manual/authentication/password_schemes/
    passhash = crypt.crypt(password, crypt.METHOD_SHA512)
    return "{SHA512-CRYPT}" + passhash


def get_mail_domain():
    with open("/etc/mailname", "r") as fp:
        return fp.read().strip()


def get_valid_email_addr(length=9, chars="2345789acdefghjkmnpqrstuvwxyz"):
    localpart = "".join(random.choice(chars) for i in range(length))
    mail_domain = get_mail_domain()
    return f"{localpart}@{mail_domain}"
