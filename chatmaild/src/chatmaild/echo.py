#!/usr/bin/env python3
"""Advanced echo bot example.

it will echo back any message that has non-empty text and also supports the /help command.
"""

import logging
import os
import sys

from deltachat_rpc_client import Bot, DeltaChat, EventType, Rpc, events

from chatmaild.config import read_config

hooks = events.HookCollection()


@hooks.on(events.RawEvent)
def log_event(event):
    if event.kind == EventType.INFO:
        logging.info("%s", event.msg)
    elif event.kind == EventType.WARNING:
        logging.warning("%s", event.msg)


@hooks.on(events.RawEvent(EventType.ERROR))
def log_error(event):
    logging.error("%s", event.msg)


@hooks.on(events.MemberListChanged)
def on_memberlist_changed(event):
    logging.info(
        "member %s was %s", event.member, "added" if event.member_added else "removed"
    )


@hooks.on(events.GroupImageChanged)
def on_group_image_changed(event):
    logging.info("group image %s", "deleted" if event.image_deleted else "changed")


@hooks.on(events.GroupNameChanged)
def on_group_name_changed(event):
    logging.info("group name changed, old name: %s", event.old_name)


@hooks.on(events.NewMessage(func=lambda e: not e.command))
def echo(event):
    snapshot = event.message_snapshot
    if snapshot.is_info:
        # Ignore info messages
        return
    if snapshot.text or snapshot.file:
        snapshot.chat.send_message(text=snapshot.text, file=snapshot.file)


@hooks.on(events.NewMessage(command="/help"))
def help_command(event):
    snapshot = event.message_snapshot
    snapshot.chat.send_text("Send me any message and I will echo it back")


def main():
    logging.basicConfig(level=logging.INFO)
    path = os.environ.get("PATH")
    venv_path = sys.argv[0].strip("echobot")
    os.environ["PATH"] = path + ":" + venv_path
    with Rpc() as rpc:
        deltachat = DeltaChat(rpc)
        system_info = deltachat.get_system_info()
        logging.info("Running deltachat core %s", system_info.deltachat_core_version)

        accounts = deltachat.get_all_accounts()
        account = accounts[0] if accounts else deltachat.add_account()

        bot = Bot(account, hooks)
        if not bot.is_configured():
            config = read_config(sys.argv[1])
            password = "eiPhiez0eo8raighoh0C"  # FIXME read from config
            email = "echo@" + config.mail_domain
            bot.configure(email, password)
        bot.run_forever()


if __name__ == "__main__":
    main()
