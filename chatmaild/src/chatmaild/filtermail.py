#!/usr/bin/env python3
import asyncio
import logging
import time
import sys
from email.parser import BytesParser
from email import policy
from email.utils import parseaddr

from aiosmtpd.lmtp import LMTP
from aiosmtpd.smtp import SMTP
from aiosmtpd.controller import UnixSocketController, Controller
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


class BeforeQueueHandler:
    def __init__(self):
        self.send_rate_limiter = SendRateLimiter()

    async def handle_MAIL(self, server, session, envelope, address, mail_options):
        logging.info(f"handle_MAIL from {address}")
        if self.send_rate_limiter.is_sending_allowed(address):
            envelope.mail_from = address
            return "250 OK"
        return f"450 4.7.1: Too much mail from {address}"

    async def handle_DATA(self, server, session, envelope):
        logging.info("handle_DATA before-queue: re-injecting the mail")
        client = SMTPClient("localhost", "10026")
        client.sendmail(envelope.mail_from, envelope.rcpt_tos, envelope.content)
        return "250 OK"


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


class AfterQueueHandler:
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        envelope.rcpt_tos.append(address)
        return "250 OK"

    async def handle_DATA(self, server, session, envelope):
        valid_recipients, res = lmtp_handle_DATA(envelope)
        # Reinject the mail back into Postfix.
        if valid_recipients:
            logging.info("afterqueue: re-injecting the mail")
            client = SMTPClient("localhost", "10027")
            client.sendmail(envelope.mail_from, valid_recipients, envelope.content)
        else:
            logging.info("no valid recipients, ignoring mail")

        return "\r\n".join(res)


def lmtp_handle_DATA(envelope):
    """the central filtering function for e-mails."""
    logging.info(f"Processing DATA message from {envelope.mail_from}")

    message = BytesParser(policy=policy.default).parsebytes(envelope.content)
    mail_encrypted = check_encrypted(message)

    valid_recipients = []
    res = []
    for recipient in envelope.rcpt_tos:
        my_local_domain = envelope.mail_from.split("@")
        if len(my_local_domain) != 2:
            res += [f"500 Invalid from address <{envelope.mail_from}>"]
            continue

        _, from_addr = parseaddr(message.get("from").strip())
        logging.info(f"mime-from: {from_addr} envelope-from: {envelope.mail_from}")
        if envelope.mail_from.lower() != from_addr.lower():
            res += [f"500 Invalid FROM <{from_addr}> for <{envelope.mail_from}>"]
            continue

        if envelope.mail_from == recipient:
            # Always allow sending emails to self.
            valid_recipients += [recipient]
            res += ["250 OK"]
            continue

        recipient_local_domain = recipient.split("@")
        if len(recipient_local_domain) != 2:
            res += [f"500 Invalid address <{recipient}>"]
            continue

        is_outgoing = recipient_local_domain[1] != my_local_domain[1]

        if (
            is_outgoing
            and not mail_encrypted
            and message.get("secure-join") != "vc-request"
            and message.get("secure-join") != "vg-request"
        ):
            res += ["500 Outgoing mail must be encrypted"]
            continue

        valid_recipients += [recipient]
        res += ["250 OK"]

    assert len(envelope.rcpt_tos) == len(res)
    assert len(valid_recipients) <= len(res)
    return valid_recipients, res


class UnixController(UnixSocketController):
    def factory(self):
        return LMTP(self.handler, **self.SMTP_kwargs)


class SMTPController(Controller):
    def factory(self):
        return SMTP(self.handler, **self.SMTP_kwargs)


async def asyncmain_afterqueue(loop, unix_socket_fn):
    UnixController(AfterQueueHandler(), unix_socket=unix_socket_fn).start()


async def asyncmain_beforequeue(loop, port):
    Controller(BeforeQueueHandler(), hostname="127.0.0.1", port=port).start()


def main():
    args = sys.argv[1:]
    assert len(args) == 2
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if args[0] == "afterqueue":
        task = asyncmain_afterqueue(loop, args[1])
    elif args[0] == "beforequeue":
        task = asyncmain_beforequeue(loop, port=int(args[1]))
    else:
        raise SystemExit(1)
    loop.create_task(task)
    loop.run_forever()
