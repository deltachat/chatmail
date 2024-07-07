"""
Functions to be executed on an ssh-connected host.

All functions of this module need to work with Python builtin types
and standard library dependencies only.

When a remote function executes remotely, it runs in a system python interpreter
without any installed dependencies.

"""

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
        f"openssl rsa -in /etc/dkimkeys/{dkim_selector}.private"
        "-pubout 2>/dev/null | awk '/-/{next}{printf(\"%s\",$0)}'"
    )
    dkim_entry_value = f"v=DKIM1;k=rsa;p={dkim_pubkey};s=email;t=s"
    dkim_entry_str = ""
    while len(dkim_entry_value) >= 255:
        dkim_entry_str += '"' + dkim_entry_value[:255] + '" '
        dkim_entry_value = dkim_entry_value[255:]
    dkim_entry_str += '"' + dkim_entry_value + '"'
    return f"{dkim_selector}._domainkey.{mail_domain}. TXT {dkim_entry_str}"


def get_ip_address_and_reverse(typ):
    sock = socket.socket(typ, socket.SOCK_DGRAM)
    sock.settimeout(0)
    sock.connect(("notifications.delta.chat", 1))
    ip = sock.getsockname()[0]
    return ip, shell(f"dig -r -x {ip} +short").rstrip(".")


def query_dns(typ, domain):
    res = shell(f"dig -r -q {domain} -t {typ} +short")
    return res.partition("\n")[0]


def check_zonefile(zonefile):
    diff = []

    for line in zonefile.splitlines():
        for typ in ["A", "AAAA", "CNAME", "CAA"]:
            if f" {typ} " in line:
                domain, value = line.split(f" {typ} ")
                current = query_dns(typ, domain.strip()[:-1])
                if current != value.strip():
                    diff.append(line)
        if " MX " in line:
            domain, typ, prio, value = line.split()
            current = query_dns(typ, domain[:-1])
            if not current:
                diff.append(line)
            elif current.split()[1] != value:
                diff.append(line.replace(prio, str(int(current[0]) + 1)))
        if " SRV " in line:
            domain, typ, prio, weight, port, value = line.split()
            current = query_dns("SRV", domain[:-1])
            if current != f"{prio} {weight} {port} {value}":
                diff.append(line)
        if " TXT " in line:
            domain, value = line.split(" TXT ")
            current = query_dns("TXT", domain.strip()[:-1])
            if domain.startswith("_mta-sts."):
                if current:
                    if current.split("id=")[0] == value.split("id=")[0]:
                        continue

            # TXT records longer than 255 bytes
            # are split into multiple <character-string>s.
            # This typically happens with DKIM record
            # which contains long RSA key.
            #
            # Removing `" "` before comparison
            # to get back a single string.
            if current.replace('" "', "") != value.replace('" "', ""):
                diff.append(line)

    return diff


# check if this module is executed remotely
# and setup a simple serialized function-execution loop

if __name__ == "__channelexec__":
    while 1:
        func_name, kwargs = channel.receive()  # noqa
        channel.send(globals()[func_name](**kwargs))  # noqa
