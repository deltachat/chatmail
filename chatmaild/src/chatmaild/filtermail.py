#!/usr/bin/env python3
import asyncio
import base64
import binascii
import logging
import sys
import time
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr
from smtplib import SMTP as SMTPClient

from aiosmtpd.controller import Controller

from .common_encrypted_subjects import common_encrypted_subjects
from .config import read_config


def check_openpgp_payload(payload: bytes):
    """Checks the OpenPGP payload.

    OpenPGP payload must consist only of PKESK and SKESK packets
    terminated by a single SEIPD packet.

    Returns True if OpenPGP payload is correct,
    False otherwise.

    May raise IndexError while trying to read OpenPGP packet header
    if it is truncated.
    """
    i = 0
    while i < len(payload):
        # Only OpenPGP format is allowed.
        if payload[i] & 0xC0 != 0xC0:
            return False

        packet_type_id = payload[i] & 0x3F
        i += 1
        if payload[i] < 192:
            # One-octet length.
            body_len = payload[i]
            i += 1
        elif payload[i] < 224:
            # Two-octet length.
            body_len = ((payload[i] - 192) << 8) + payload[i + 1] + 192
            i += 2
        elif payload[i] == 255:
            # Five-octet length.
            body_len = (
                (payload[i + 1] << 24)
                | (payload[i + 2] << 16)
                | (payload[i + 3] << 8)
                | payload[i + 4]
            )
            i += 5
        else:
            # Partial body length is not allowed.
            return False

        i += body_len

        if i == len(payload):
            if packet_type_id == 18:
                # Last packet should be
                # Symmetrically Encrypted and Integrity Protected Data Packet (SEIPD)
                return True
        elif packet_type_id not in [1, 3]:
            # All packets except the last one must be either
            # Public-Key Encrypted Session Key Packet (PKESK)
            # or
            # Symmetric-Key Encrypted Session Key Packet (SKESK)
            return False

    if i == 0:
        return False

    if i > len(payload):
        # Payload is truncated.
        return False
    return True


def check_armored_payload(payload: str):
    prefix = "-----BEGIN PGP MESSAGE-----\r\n\r\n"
    if not payload.startswith(prefix):
        return False
    payload = payload.removeprefix(prefix)

    suffix = "-----END PGP MESSAGE-----\r\n\r\n"
    if not payload.endswith(suffix):
        return False
    payload = payload.removesuffix(suffix)

    # Remove CRC24.
    payload = payload.rpartition("=")[0]

    try:
        payload = base64.b64decode(payload)
    except binascii.Error:
        return False

    try:
        return check_openpgp_payload(payload)
    except IndexError:
        return False


def check_encrypted(message):
    """Check that the message is an OpenPGP-encrypted message.

    MIME structure of the message must correspond to <https://www.rfc-editor.org/rfc/rfc3156>.
    """
    if not message.is_multipart():
        return False
    if message.get("subject") not in common_encrypted_subjects:
        return False
    if message.get_content_type() != "multipart/encrypted":
        return False
    parts_count = 0
    for part in message.iter_parts():
        # We explicitly check Content-Type of each part later,
        # but this is to be absolutely sure `get_payload()` returns string and not list.
        if part.is_multipart():
            return False

        if parts_count == 0:
            if part.get_content_type() != "application/pgp-encrypted":
                return False

            payload = part.get_payload()
            if payload.strip() != "Version: 1":
                return False
        elif parts_count == 1:
            if part.get_content_type() != "application/octet-stream":
                return False

            if not check_armored_payload(part.get_payload()):
                return False
        else:
            return False
        parts_count += 1
    return True


async def asyncmain_beforequeue(config):
    port = config.filtermail_smtp_port
    Controller(BeforeQueueHandler(config), hostname="127.0.0.1", port=port).start()


class BeforeQueueHandler:
    def __init__(self, config):
        self.config = config
        self.send_rate_limiter = SendRateLimiter()

    async def handle_MAIL(self, server, session, envelope, address, mail_options):
        logging.info(f"handle_MAIL from {address}")
        envelope.mail_from = address
        max_sent = self.config.max_user_send_per_minute
        if not self.send_rate_limiter.is_sending_allowed(address, max_sent):
            return f"450 4.7.1: Too much mail from {address}"

        parts = envelope.mail_from.split("@")
        if len(parts) != 2:
            return f"500 Invalid from address <{envelope.mail_from!r}>"

        return "250 OK"

    async def handle_DATA(self, server, session, envelope):
        logging.info("handle_DATA before-queue")
        error = self.check_DATA(envelope)
        if error:
            return error
        logging.info("re-injecting the mail that passed checks")
        client = SMTPClient("localhost", self.config.postfix_reinject_port)
        client.sendmail(envelope.mail_from, envelope.rcpt_tos, envelope.content)
        return "250 OK"

    def check_DATA(self, envelope):
        """the central filtering function for e-mails."""
        logging.info(f"Processing DATA message from {envelope.mail_from}")

        message = BytesParser(policy=policy.default).parsebytes(envelope.content)
        mail_encrypted = check_encrypted(message)

        _, from_addr = parseaddr(message.get("from").strip())
        logging.info(f"mime-from: {from_addr} envelope-from: {envelope.mail_from!r}")
        if envelope.mail_from.lower() != from_addr.lower():
            return f"500 Invalid FROM <{from_addr!r}> for <{envelope.mail_from!r}>"

        if envelope.mail_from in self.config.passthrough_senders:
            return

        passthrough_recipients = self.config.passthrough_recipients
        envelope_from_domain = from_addr.split("@").pop()
        for recipient in envelope.rcpt_tos:
            if envelope.mail_from == recipient:
                # Always allow sending emails to self.
                continue
            if recipient in passthrough_recipients:
                continue
            res = recipient.split("@")
            if len(res) != 2:
                return f"500 Invalid address <{recipient}>"
            _recipient_addr, recipient_domain = res

            is_outgoing = recipient_domain != envelope_from_domain
            if is_outgoing and not mail_encrypted:
                is_securejoin = message.get("secure-join") in [
                    "vc-request",
                    "vg-request",
                ]
                if not is_securejoin:
                    return f"500 Invalid unencrypted mail to <{recipient}>"


class SendRateLimiter:
    def __init__(self):
        self.addr2timestamps = {}

    def is_sending_allowed(self, mail_from, max_send_per_minute):
        last = self.addr2timestamps.setdefault(mail_from, [])
        now = time.time()
        last[:] = [ts for ts in last if ts >= (now - 60)]
        if len(last) <= max_send_per_minute:
            last.append(now)
            return True
        return False


def main():
    args = sys.argv[1:]
    assert len(args) == 1
    config = read_config(args[0])
    logging.basicConfig(level=logging.WARN)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    task = asyncmain_beforequeue(config)
    loop.create_task(task)
    loop.run_forever()
