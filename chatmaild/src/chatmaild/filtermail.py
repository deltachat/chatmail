#!/usr/bin/env python3
import asyncio
import logging
import time
import sys
from email.parser import BytesParser
from email import policy
from email.utils import parseaddr

from aiosmtpd.smtp import SMTP
from aiosmtpd.controller import Controller
from smtplib import SMTP as SMTPClient


def check_encrypted(message):
    """Check that the message is an OpenPGP-encrypted message."""
    if not message.is_multipart():
        return False
    if message.get("subject") != "...":
        return False
    if message.get_content_type() != "multipart/encrypted":
        return False
    parts_count = 0
    for part in message.iter_parts():
        if parts_count == 0:
            if part.get_content_type() != "application/pgp-encrypted":
                return False
        elif parts_count == 1:
            if part.get_content_type() != "application/octet-stream":
                return False
        else:
            return False
        parts_count += 1
    return True


def check_mdn(message, envelope):
    if len(envelope.rcpt_tos) != 1:
        return False

    for name in ["auto-submitted", "chat-version"]:
        if not message.get(name):
            return False

    if message.get_content_type() != "multipart/report":
        return False

    body = message.get_body()
    if body.get_content_type() != "text/plain":
        return False

    if list(body.iter_attachments()) or list(body.iter_parts()):
        return False

    # even with all mime-structural checks an attacker
    # could try to abuse the subject or body to contain links or other
    # annoyance -- we skip on checking subject/body for now as Delta Chat
    # should evolve to create E2E-encrypted read receipts anyway.
    # and then MDNs are just encrypted mail and can pass the border
    # to other instances.

    return True


class SMTPController(Controller):
    def factory(self):
        return SMTP(self.handler, **self.SMTP_kwargs)


class BeforeQueueHandler:
    def __init__(self):
        self.send_rate_limiter = SendRateLimiter()

    async def handle_MAIL(self, server, session, envelope, address, mail_options):
        logging.info(f"handle_MAIL from {address}")
        envelope.mail_from = address
        if not self.send_rate_limiter.is_sending_allowed(address):
            return f"450 4.7.1: Too much mail from {address}"

        parts = envelope.mail_from.split("@")
        if len(parts) != 2:
            return f"500 Invalid from address <{envelope.mail_from!r}>"

        return "250 OK"

    async def handle_DATA(self, server, session, envelope):
        logging.info("handle_DATA before-queue")
        error = check_DATA(envelope)
        if error:
            return error
        logging.info("re-injecting the mail that passed checks")
        client = SMTPClient("localhost", "10025")
        client.sendmail(envelope.mail_from, envelope.rcpt_tos, envelope.content)
        return "250 OK"


async def asyncmain_beforequeue(port):
    Controller(BeforeQueueHandler(), hostname="127.0.0.1", port=port).start()


def check_DATA(envelope):
    """the central filtering function for e-mails."""
    logging.info(f"Processing DATA message from {envelope.mail_from}")

    message = BytesParser(policy=policy.default).parsebytes(envelope.content)
    mail_encrypted = check_encrypted(message)

    _, from_addr = parseaddr(message.get("from").strip())
    logging.info(f"mime-from: {from_addr} envelope-from: {envelope.mail_from!r}")
    if envelope.mail_from.lower() != from_addr.lower():
        return f"500 Invalid FROM <{from_addr!r}> for <{envelope.mail_from!r}>"

    if not mail_encrypted and check_mdn(message, envelope):
        return

    envelope_from_domain = from_addr.split("@").pop()
    for recipient in envelope.rcpt_tos:
        if envelope.mail_from == recipient:
            # Always allow sending emails to self.
            continue
        res = recipient.split("@")
        if len(res) != 2:
            return f"500 Invalid address <{recipient}>"
        _recipient_addr, recipient_domain = res

        is_outgoing = recipient_domain != envelope_from_domain
        if is_outgoing and not mail_encrypted:
            is_securejoin = message.get("secure-join") in ["vc-request", "vg-request"]
            if not is_securejoin:
                return f"500 Invalid unencrypted mail to <{recipient}>"


class SendRateLimiter:
    MAX_USER_SEND_PER_MINUTE = 80

    def __init__(self):
        self.addr2timestamps = {}

    def is_sending_allowed(self, mail_from):
        last = self.addr2timestamps.setdefault(mail_from, [])
        now = time.time()
        last[:] = [ts for ts in last if ts >= (now - 60)]
        if len(last) <= self.MAX_USER_SEND_PER_MINUTE:
            last.append(now)
            return True
        return False


def main():
    args = sys.argv[1:]
    assert len(args) == 1
    logging.basicConfig(level=logging.WARN)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = asyncmain_beforequeue(port=int(args[0]))
    loop.create_task(task)
    loop.run_forever()
