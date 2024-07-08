import datetime
import importlib

from . import remote_funcs
from .sshexec import SSHExec


def show_dns(args, out) -> int:
    """Check existing DNS records, optionally write them to zone file
    and return exit code 0 for success, non-zero otherwise."""
    print("Checking your DKIM keys and DNS entries...")
    template = importlib.resources.files(__package__).joinpath("chatmail.zone.f")
    mail_domain = args.config.mail_domain

    sshexec = SSHExec(mail_domain, remote_funcs)

    remote_data = sshexec(remote_funcs.perform_initial_checks, mail_domain=mail_domain)

    assert remote_data["ipv4"] or remote_data["ipv6"]

    with open(template, "r") as f:
        zonefile = f.read().format(
            acme_account_url=remote_data["acme_account_url"],
            dkim_entry=remote_data["dkim_entry"],
            ipv6=remote_data["ipv6"],
            ipv4=remote_data["ipv4"],
            sts_id=datetime.datetime.now().strftime("%Y%m%d%H%M"),
            chatmail_domain=args.config.mail_domain,
        )
    if getattr(args, "zonefile", None):
        with open(args.zonefile, "w+") as zf:
            zf.write(zonefile)
        print(f"DNS records successfully written to: {args.zonefile}")

    to_print = sshexec(remote_funcs.check_zonefile, zonefile=zonefile)

    if to_print:
        to_print.insert(
            0, "You should configure the following entries at your DNS provider:\n"
        )
        to_print.append(
            "\nIf you already configured the DNS entries, wait a bit until the DNS entries propagate to the Internet."
        )
        out.red("\n".join(to_print))
        exit_code = 1
    else:
        out.green("Great! All your DNS entries are verified and correct.")
        exit_code = 0

    to_print = []
    if not remote_data["reverse_ipv4"]:
        to_print.append(f"\tIPv4:\t{remote_data['ipv4']}\t{args.config.mail_domain}")
    if not remote_data["reverse_ipv6"]:
        to_print.append(f"\tIPv6:\t{remote_data['ipv6']}\t{args.config.mail_domain}")
    if len(to_print) > 0:
        out.red("You need to set the following PTR/reverse DNS data:")
        for entry in to_print:
            print(entry)
        out.red(
            "You can do so at your hosting provider (maybe this isn't your DNS provider)."
        )

    return exit_code
