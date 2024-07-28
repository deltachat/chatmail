import datetime
import importlib

from jinja2 import Template

from . import remote_funcs


def get_initial_remote_data(sshexec, mail_domain):
    return sshexec.logged(
        call=remote_funcs.perform_initial_checks, kwargs=dict(mail_domain=mail_domain)
    )


def check_initial_remote_data(remote_data, print=print):
    mail_domain = remote_data["mail_domain"]
    if not remote_data["A"] and not remote_data["AAAA"]:
        print(f"Missing A and/or AAAA DNS records for {mail_domain}!")
    elif not remote_data["MTA_STS"]:
        print("Missing MTA-STS CNAME record:")
        print(f"mta-sts.{mail_domain}.   CNAME  {mail_domain}")
    else:
        return remote_data


def get_filled_zone_file(remote_data):
    sts_id = remote_data.get("sts_id")
    if not sts_id:
        sts_id = datetime.datetime.now().strftime("%Y%m%d%H%M")

    template = importlib.resources.files(__package__).joinpath("chatmail.zone.j2")
    content = template.read_text()
    zonefile = Template(content).render(**remote_data)
    lines = [x.strip() for x in zonefile.split("\n") if x.strip()]
    lines.append("")
    zonefile = "\n".join(lines)
    return zonefile


def check_full_zone(sshexec, remote_data, out, zonefile) -> int:
    """Check existing DNS records, optionally write them to zone file
    and return (exitcode, remote_data) tuple."""

    required_diff, recommended_diff = sshexec.logged(
        remote_funcs.check_zonefile, kwargs=dict(zonefile=zonefile)
    )

    if required_diff:
        out.red("Please set required DNS entries at your DNS provider:\n")
        for line in required_diff:
            out(line)
        return 1
    elif recommended_diff:
        out("WARNING: these recommended DNS entries are not set:\n")
        for line in recommended_diff:
            out(line)
        return 0

    out.green("Great! All your DNS entries are verified and correct.")
    return 0
