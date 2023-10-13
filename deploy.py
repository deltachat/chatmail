import os
from pyinfra import host, facts
from chatmail import deploy_chatmail


def main():
    mail_domain = os.getenv("CHATMAIL_DOMAIN")
    mail_server = os.getenv("CHATMAIL_SERVER", mail_domain)
    dkim_selector = os.getenv("CHATMAIL_DKIM_SELECTOR", "2023")

    assert mail_domain
    assert mail_server
    assert dkim_selector

    deploy_chatmail(mail_domain, mail_server, dkim_selector)


main()
