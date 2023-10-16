#!/usr/bin/env python3
import asyncio
import logging
from email.parser import BytesParser
from email import policy

from aiosmtpd.lmtp import LMTP
from aiosmtpd.controller import UnixSocketController
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


class ExampleController(UnixSocketController):
    def factory(self):
        return LMTP(self.handler, **self.SMTP_kwargs)


class ExampleHandler:
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        envelope.rcpt_tos.append(address)
        return "250 OK"

    async def handle_DATA(self, server, session, envelope):
        logging.info("Processing DATA message from %s", envelope.mail_from)

        valid_recipients = []

        message = BytesParser(policy=policy.default).parsebytes(envelope.content)
        mail_encrypted = check_encrypted(message)

        res = []
        for recipient in envelope.rcpt_tos:
            my_local_domain = envelope.mail_from.split("@")
            if len(my_local_domain) != 2:
                res += [f"500 Invalid from address <{envelope.mail_from}>"]
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

        # Reinject the mail back into Postfix.
        if valid_recipients:
            logging.info("Reinjecting the mail")
            client = SMTPClient("localhost", "10026")
            client.sendmail(envelope.mail_from, valid_recipients, envelope.content)

        return "\r\n".join(res)


async def asyncmain(loop):
    controller = ExampleController(
        ExampleHandler(), unix_socket="/var/spool/postfix/private/filtermail"
    )
    controller.start()


def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.create_task(asyncmain(loop=loop))
    loop.run_forever()


if __name__ == "__main__":
    main()
