"""
Pure python functions which execute remotely in a system Python interpreter.

All functions of this module

- need to get and and return Python builtin data types only,

- can only use standard library dependencies,

- can freely call each other.
"""

import re

from .rshell import CalledProcessError, shell


def perform_initial_checks(mail_domain):
    """Collecting initial DNS settings."""
    assert mail_domain
    if not shell("dig", fail_ok=True):
        shell("apt-get install -y dnsutils")
    shell(f"unbound-control flush_zone {mail_domain}", fail_ok=True)
    A = query_dns("A", mail_domain)
    AAAA = query_dns("AAAA", mail_domain)
    MTA_STS = query_dns("CNAME", f"mta-sts.{mail_domain}")
    WWW = query_dns("CNAME", f"www.{mail_domain}")

    res = dict(mail_domain=mail_domain, A=A, AAAA=AAAA, MTA_STS=MTA_STS, WWW=WWW)
    if not MTA_STS or not WWW or (not A and not AAAA):
        return res

    res["acme_account_url"] = shell("acmetool account-url", fail_ok=True)
    res["dkim_entry"] = get_dkim_entry(mail_domain, dkim_selector="opendkim")

    # parse out sts-id if exists, example: "v=STSv1; id=2090123"
    parts = query_dns("TXT", f"_mta-sts.{mail_domain}").split("id=")
    res["sts_id"] = parts[1].rstrip('"') if len(parts) == 2 else ""
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
    return ""


def check_zonefile(zonefile, mail_domain):
    """Check expected zone file entries."""
    shell(f"unbound-control flush_zone {mail_domain}", fail_ok=True)
    required = True
    required_diff = []
    recommended_diff = []

    for zf_line in zonefile.splitlines():
        if "; Recommended" in zf_line:
            required = False
            continue
        if not zf_line.strip() or zf_line.startswith(";"):
            continue
        print(f"dns-checking {zf_line!r}")
        zf_domain, zf_typ, zf_value = zf_line.split(maxsplit=2)
        zf_domain = zf_domain.rstrip(".")
        zf_value = zf_value.strip()
        query_value = query_dns(zf_typ, zf_domain)
        if zf_value != query_value:
            assert zf_typ in ("A", "AAAA", "CNAME", "CAA", "SRV", "MX", "TXT"), zf_line
            if required:
                required_diff.append(zf_line)
            else:
                recommended_diff.append(zf_line)

    return required_diff, recommended_diff
