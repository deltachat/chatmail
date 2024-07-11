import datetime
import importlib

from jinja2 import Template

from . import remote_funcs


def get_initial_remote_data(args, out):
    sshexec = args.get_sshexec()
    mail_domain = args.config.mail_domain
    return sshexec.logged(
        call=remote_funcs.perform_initial_checks, kwargs=dict(mail_domain=mail_domain)
    )


def check_initial_remote_data(remote_data, print=print):
    mail_domain = remote_data["mail_domain"]
    if not remote_data["A"] and not remote_data["AAAA"]:
        print("Missing A and/or AAAA DNS records for {mail_domain}!")
    elif not remote_data["MTA_STS"]:
        print("Missing MTA-STS CNAME record:")
        print(f"mta-sts.{mail_domain}.   CNAME  {mail_domain}")
    else:
        return remote_data


def show_dns(args, out, remote_data) -> int:
    """Check existing DNS records, optionally write them to zone file
    and return (exitcode, remote_data) tuple."""

    sshexec = args.get_sshexec()

    if not remote_data["acme_account_url"]:
        out.red("could not get letsencrypt account url, please run 'cmdeploy run'")
        return 1

    if not remote_data["dkim_entry"]:
        out.red("could not determine dkim_entry, please run 'cmdeploy run'")
        return 1

    sts_id = remote_data.get("sts_id")
    if not sts_id:
        sts_id = datetime.datetime.now().strftime("%Y%m%d%H%M")

    template = importlib.resources.files(__package__).joinpath("chatmail.zone.j2")
    content = template.read_text()
    zonefile = Template(content).render(
        acme_account_url=remote_data.get("acme_account_url"),
        dkim_entry=remote_data["dkim_entry"],
        ipv4=remote_data["A"],
        ipv6=remote_data["AAAA"],
        sts_id=sts_id,
        chatmail_domain=args.config.mail_domain,
    )
    lines = [x.strip() for x in zonefile.split("\n") if x.strip()]
    lines.append("")
    zonefile = "\n".join(lines)

    diff_records = sshexec.logged(
        remote_funcs.check_zonefile, kwargs=dict(zonefile=zonefile)
    )

    if getattr(args, "zonefile", None):
        with open(args.zonefile, "w+") as zf:
            zf.write(zonefile)
        out.green(f"DNS records successfully written to: {args.zonefile}")
        return 0

    if diff_records:
        out.red("Please set the following DNS entries at your DNS provider:\n")
        for line in diff_records:
            out(line)
        return 1
    else:
        out.green("Great! All your DNS entries are verified and correct.")
        return 0
