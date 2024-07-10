import datetime
import importlib
import sys

from jinja2 import Template

from . import remote_funcs


class NoIPRecords(Exception):
    """Indicates that no DNS A or AAAA record is present."""


def show_dns(args, out) -> int:
    """Check existing DNS records, optionally write them to zone file
    and return (exitcode, remote_data) tuple."""
    template = importlib.resources.files(__package__).joinpath("chatmail.zone.j2")
    mail_domain = args.config.mail_domain

    def log_progress(data):
        sys.stdout.write(".")
        sys.stdout.flush()

    sshexec = args.get_sshexec(log=print if args.verbose else log_progress)
    print("Checking DNS entries ", end="\n" if args.verbose else "")

    remote_data = sshexec(remote_funcs.perform_initial_checks, mail_domain=mail_domain)

    if not remote_data["ipv4"] and not remote_data["ipv6"]:
        raise NoIPRecords(f"No A or AAAA DNS records set for {mail_domain}!")

    sts_id = remote_data.get("sts_id")
    if not sts_id:
        sts_id = datetime.datetime.now().strftime("%Y%m%d%H%M")

    content = template.read_text()
    zonefile = Template(content).render(
        acme_account_url=remote_data.get("acme_account_url"),
        dkim_entry=remote_data.get("dkim_entry"),
        ipv4=remote_data["ipv4"],
        ipv6=remote_data["ipv6"],
        sts_id=sts_id,
        chatmail_domain=args.config.mail_domain,
    )
    zonefile = "\n".join([x.strip() for x in zonefile.split("\n") if x.strip()])

    to_print = sshexec(remote_funcs.check_zonefile, zonefile=zonefile)
    if not args.verbose:
        print()

    if getattr(args, "zonefile", None):
        with open(args.zonefile, "w+") as zf:
            zf.write(zonefile)
        out.green(f"DNS records successfully written to: {args.zonefile}")
        return 0, remote_data

    if to_print:
        to_print.insert(
            0, "You should configure the following entries at your DNS provider:\n"
        )
        to_print.append(
            "\nIf you already configured the DNS entries, "
            "wait a bit until the DNS entries propagate to the Internet."
        )
        out.red("\n".join(to_print))
        exit_code = 1
    else:
        out.green("Great! All your DNS entries are verified and correct.")
        exit_code = 0

    return exit_code, remote_data
