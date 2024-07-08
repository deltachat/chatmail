"""
Functions to be executed on an ssh-connected host.

All functions of this module need to work with Python builtin types
and standard library dependencies only.

When a remote function executes remotely, it runs in a system python interpreter
without any installed dependencies.

"""

import re
import socket
from subprocess import check_output


def shell(command):
    return check_output(command, shell=True).decode().rstrip()


def get_systemd_running():
    lines = shell("systemctl --type=service --state=running").split("\n")
    return [line for line in lines if line.startswith("  ")]


def perform_initial_checks(mail_domain):
    res = {}

    res["acme_account_url"] = shell("acmetool account-url")
    shell("apt-get install -y dnsutils")
    shell("unbound-control flush_zone {mail_domain}")

    res["dkim_entry"] = get_dkim_entry(mail_domain, dkim_selector="opendkim")

    ipv4, reverse_ipv4 = get_ip_address_and_reverse(socket.AF_INET)
    ipv6, reverse_ipv6 = get_ip_address_and_reverse(socket.AF_INET6)
    res.update(dict(ipv4=ipv4, reverse_ipv4=reverse_ipv4))
    res.update(dict(ipv6=ipv6, reverse_ipv6=reverse_ipv6))
    return res


def get_dkim_entry(mail_domain, dkim_selector):
    dkim_pubkey = shell(
        f"openssl rsa -in /etc/dkimkeys/{dkim_selector}.private "
        "-pubout 2>/dev/null | awk '/-/{next}{printf(\"%s\",$0)}'"
    )
    dkim_value_raw = f"v=DKIM1;k=rsa;p={dkim_pubkey};s=email;t=s"
    dkim_value = '" "'.join(re.findall(".{1,255}", dkim_value_raw))
    return f'{dkim_selector}._domainkey.{mail_domain}. TXT "{dkim_value}"'


def get_ip_address_and_reverse(typ):
    sock = socket.socket(typ, socket.SOCK_DGRAM)
    sock.settimeout(0)
    sock.connect(("notifications.delta.chat", 1))
    ip = sock.getsockname()[0]
    return ip, shell(f"dig -r -x {ip} +short").rstrip(".")


def query_dns(typ, domain):
    res = shell(f"dig -r -q {domain} -t {typ} +short")
    return set(filter(None, res.split("\n")))


def check_zonefile(zonefile):
    diff = []

    for zf_line in zonefile.splitlines():
        zf_domain, zf_typ, zf_value = zf_line.split(maxsplit=2)
        zf_domain = zf_domain.rstrip(".")
        zf_value = zf_value.strip()
        query_values = query_dns(zf_typ, zf_domain)
        if zf_value in query_values:
            continue

        if query_values and zf_typ == "TXT" and zf_domain.startswith("_mta-sts."):
            (query_value,) = query_values
            if query_value.split("id=")[0] == zf_value.split("id=")[0]:
                continue

        assert zf_typ in ("A", "AAAA", "CNAME", "CAA", "SRV", "MX", "TXT"), zf_line
        diff.append(zf_line)

    return diff


# check if this module is executed remotely
# and setup a simple serialized function-execution loop

if __name__ == "__channelexec__":
    while 1:
        func_name, kwargs = channel.receive()  # noqa
        channel.send(globals()[func_name](**kwargs))  # noqa
