"""
Functions to be executed on an ssh-connected host.

All functions of this module need to work with Python builtin types
and standard library dependencies only.

When a remote function executes remotely, it runs in a system python interpreter
without any installed dependencies.

"""

import re
from subprocess import CalledProcessError, check_output


def shell(command, fail_ok=False):
    print(f"$ {command}")
    try:
        return check_output(command, shell=True).decode().rstrip()
    except CalledProcessError:
        if not fail_ok:
            raise
        return ""


def get_systemd_running():
    lines = shell("systemctl --type=service --state=running").split("\n")
    return [line for line in lines if line.startswith("  ")]


def perform_initial_checks(mail_domain):
    res = {}

    res["acme_account_url"] = shell("acmetool account-url", fail_ok=True)
    if not shell("dig", fail_ok=True):
        shell("apt-get install -y dnsutils")
    shell(f"unbound-control flush_zone {mail_domain}", fail_ok=True)
    res["dkim_entry"] = get_dkim_entry(mail_domain, dkim_selector="opendkim")

    res["ipv4"] = query_dns("A", mail_domain)
    res["ipv6"] = query_dns("AAAA", mail_domain)

    # parse out sts-id if exists
    val = query_dns("TXT", f"_mta-sts.{mail_domain}")
    if val:
        # "v=STSv1; id={{ sts_id }}"
        parts = val.split("id=")
        if len(parts) == 2:
            val = parts[1].rstrip('"')
    res["sts_id"] = val

    return res


def get_dkim_entry(mail_domain, dkim_selector):
    try:
        dkim_pubkey = shell(
            f"openssl rsa -in /etc/dkimkeys/{dkim_selector}.private "
            "-pubout 2>/dev/null | awk '/-/{next}{printf(\"%s\",$0)}'"
        )
    except CalledProcessError:
        return
    dkim_value_raw = f"v=DKIM1;k=rsa;p={dkim_pubkey};s=email;t=s"
    dkim_value = '" "'.join(re.findall(".{1,255}", dkim_value_raw))
    return f'{dkim_selector}._domainkey.{mail_domain}. TXT "{dkim_value}"'


def query_dns(typ, domain):
    res = shell(f"dig -r -q {domain} -t {typ} +short")
    print(res)
    if res:
        return res.split("\n")[0]


def check_zonefile(zonefile):
    diff = []

    for zf_line in zonefile.splitlines():
        print("")
        print(f"dns-checking {zf_line!r}")
        zf_domain, zf_typ, zf_value = zf_line.split(maxsplit=2)
        zf_domain = zf_domain.rstrip(".")
        zf_value = zf_value.strip()
        query_value = query_dns(zf_typ, zf_domain)
        if zf_value != query_value:
            assert zf_typ in ("A", "AAAA", "CNAME", "CAA", "SRV", "MX", "TXT"), zf_line
            diff.append(zf_line)

    return diff


# check if this module is executed remotely
# and setup a simple serialized function-execution loop

if __name__ == "__channelexec__":

    def print(item):
        channel.send(("log", item))  # noqa

    while 1:
        func_name, kwargs = channel.receive()  # noqa
        res = globals()[func_name](**kwargs)  # noqa
        channel.send(("finish", res))  # noqa
