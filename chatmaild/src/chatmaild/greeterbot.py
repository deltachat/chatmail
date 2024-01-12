import time

import deltachat
from deltachat.tracker import ConfigureFailed
from time import sleep
import tempfile
import os
import configargparse
import pkg_resources
import secrets

from chatmaild.database import Database
from chatmaild.config import read_config
from chatmaild.newemail import ALPHANUMERIC_PUNCT, CONFIG_PATH

PASSDB_PATH = "/home/vmail/passdb.sqlite"


def setup_account(data_dir: str, debug: bool) -> deltachat.Account:
    """Create a deltachat account with a given addr/password combination.

    :param data_dir: the directory where the data(base) is stored.
    :param debug: whether to show log messages for the account.
    :return: the deltachat account object.
    """
    chatmail_config = read_config(CONFIG_PATH)
    addr = "hello@" + chatmail_config.mail_domain

    try:
        os.mkdir(os.path.join(data_dir, addr))
    except FileExistsError:
        pass
    db_path = os.path.join(data_dir, addr, "db.sqlite")

    ac = deltachat.Account(db_path)
    if debug:
        ac.add_account_plugin(deltachat.events.FFIEventLogger(ac))

    ac.set_config("mvbox_move", "0")
    ac.set_config("sentbox_watch", "0")
    ac.set_config("bot", "1")
    ac.set_config("mdns_enabled", "0")

    if not ac.is_configured():
        cleartext_password = "".join(
            secrets.choice(ALPHANUMERIC_PUNCT)
            for _ in range(chatmail_config.password_min_length + 3)
        )
        ac.set_config("mail_pw", cleartext_password)
        ac.set_config("addr", addr)

        configtracker = ac.configure()
        try:
            configtracker.wait_finish()
        except ConfigureFailed as e:
            print(
                "configuration setup failed for %s with password:\n%s"
                % (ac.get_config("addr"), ac.get_config("mail_pw"))
            )
            raise

    ac.start_io()
    avatar = pkg_resources.resource_filename(__name__, "avatar.jpg")
    ac.set_avatar(avatar)
    ac.set_config("displayname", "Hello at try.webxdc.org!")
    return ac


class GreetBot:
    def __init__(self, passdb, account):
        self.db = Database(passdb, read_only=True)
        self.account = account
        self.domain = account.get_config("addr").split("@")[1]
        with self.db.read_connection() as conn:
            self.existing_users = conn.get_user_list()

    def greet_users(self):
        with self.db.read_connection() as conn:
            users = conn.get_user_list()
        new_users = users.difference(self.existing_users)
        self.existing_users = users
        time.sleep(20)  # wait until Delta is configured on the user side
        for user in new_users:
            for ci_prefix in ["ac1_", "ac2_", "ac3_", "ac4_", "ac5_", "ci-"]:
                if user.startswith(ci_prefix):
                    continue
            if user not in [c.addr for c in self.account.get_contacts()]:
                print("Inviting", user)
                contact = self.account.create_contact(user)
                chat = contact.create_chat()
                chat.send_text("Welcome to %s! Here you can try out Delta Chat." % (self.domain,))
                chat.send_text("I prepared some webxdc apps for you, if you are interested:")
                chat.send_file(pkg_resources.resource_filename(__name__, "editor.xdc"))
                chat.send_file(pkg_resources.resource_filename(__name__, "tower-builder.xdc"))
                chat.send_text(
                    "You can send a message to xstore@testrun.org to discover more apps! "
                    "Some of these games you can also play with friends, directly in the chat."
                )


def main():
    args = configargparse.ArgumentParser()
    args.add_argument("--db_path", help="location of the Delta Chat database")
    args.add_argument("--passdb", default=PASSDB_PATH, help="location of the chatmail passdb")
    args.add_argument("--show-ffi", action="store_true", help="print Delta Chat log")
    ops = args.parse_args()

    # ensuring account data directory
    if ops.db_path is None:
        tempdir = tempfile.TemporaryDirectory(prefix="hellobot")
        ops.db_path = tempdir.name
    elif not os.path.exists(ops.db_path):
        os.mkdir(ops.db_path)

    ac = setup_account(ops.db_path, ops.show_ffi)
    greeter = GreetBot(ops.passdb, ac)
    print("waiting for new chatmail users...")
    while 1:
        greeter.greet_users()
        sleep(5)


if __name__ == "__main__":
    main()
