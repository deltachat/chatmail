import ipaddress

import requests
import importlib
import subprocess
import datetime
from ipaddress import ip_address


class DNS:
    def __init__(self, out, mail_domain):
        self.session = requests.Session()
        self.out = out
        self.ssh = f"ssh root@{mail_domain}"
        try:
            self.shell(f"unbound-control flush {mail_domain}")
        except subprocess.CalledProcessError:
            pass

    def shell(self, cmd):
        return self.out.shell_output(f"{self.ssh} -- {cmd}", no_print=True)

    def get_ipv4(self):
        cmd = "ip a | grep 'inet ' | grep 'scope global' | grep -oE '[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}' | head -1"
        return self.shell(cmd).strip()

    def get_ipv6(self):
        cmd = "ip a | grep inet6 | grep 'scope global' | sed -e 's#/64 scope global##' | sed -e 's#inet6##'"
        return self.shell(cmd).strip()

    def get(self, typ: str, domain: str) -> str:
        """Get a DNS entry"""
        dig_result = self.shell(f"dig {typ} {domain}")
        line_num = 0
        for line in dig_result.splitlines():
            line_num += 1
            if line.strip() == ";; ANSWER SECTION:":
                return dig_result.splitlines()[line_num].split("\t")[-1]

    def resolve(self, domain: str) -> str:
        result = self.get("A", domain)
        try:
            assert ipaddress.ip_address(result).version == 4
        except ValueError:
            result = self.get("CNAME", domain)
            return self.resolve(result)
        except AssertionError:
            result = self.get("AAAA", domain)
        return result

    def check_ptr_record(self, ip: str, mail_domain) -> str:
        """Check the PTR record for an IPv4 or IPv6 address."""
        result = self.get("PTR", ip_address(ip).reverse_pointer)
        return result[:-1] == mail_domain


def show_dns(args, out):
    template = importlib.resources.files(__package__).joinpath("chatmail.zone.f")
    mail_domain = args.config.mail_domain
    ssh = f"ssh root@{mail_domain}"
    dns = DNS(out, mail_domain)

    def read_dkim_entries(entry):
        lines = []
        for line in entry.split("\n"):
            if line.startswith(";") or not line.strip():
                continue
            line = line.replace("\t", " ")
            lines.append(line)
        return "\n".join(lines)

    print("Checking your DKIM keys and DNS entries...")
    acme_account_url = out.shell_output(f"{ssh} -- acmetool account-url")
    dkim_entry = read_dkim_entries(out.shell_output(f"{ssh} -- opendkim-genzone -F"))

    ipv6 = dns.get_ipv6()
    reverse_ipv6 = dns.check_ptr_record(ipv6, args.config.mail_domain)
    ipv4 = dns.get_ipv4()
    reverse_ipv4 = dns.check_ptr_record(ipv4, args.config.mail_domain)
    to_print = []

    with open(template, "r") as f:
        zonefile = (
            f.read()
            .format(
                acme_account_url=acme_account_url,
                email=f"root@{args.config.mail_domain}",
                sts_id=datetime.datetime.now().strftime("%Y%m%d%H%M"),
                chatmail_domain=args.config.mail_domain,
                dkim_entry=dkim_entry,
                ipv6=ipv6,
                ipv4=ipv4,
            )
            .strip()
        )
        if args.zonefile:
            with open(args.zonefile, "w+") as zf:
                zf.write(zonefile)
            print(f"DNS records successfully written to: {args.zonefile}")
            return
        started_dkim_parsing = False
        for line in zonefile.splitlines():
            line = line.format(
                acme_account_url=acme_account_url,
                email=f"root@{args.config.mail_domain}",
                sts_id=datetime.datetime.now().strftime("%Y%m%d%H%M"),
                chatmail_domain=args.config.mail_domain,
                dkim_entry=dkim_entry,
                ipv6=ipv6,
            ).strip()
            for typ in ["A", "AAAA", "CNAME", "CAA"]:
                if f" {typ} " in line:
                    domain, value = line.split(f" {typ} ")
                    current = dns.get(typ, domain.strip()[:-1])
                    if current != value.strip():
                        to_print.append(line)
            if " MX " in line:
                domain, typ, prio, value = line.split()
                current = dns.get(typ, domain[:-1])
                if not current:
                    to_print.append(line)
                elif current.split()[1] != value:
                    print(line.replace(prio, str(int(current[0]) + 1)))
            if " SRV " in line:
                domain, typ, prio, weight, port, value = line.split()
                current = dns.get("SRV", domain[:-1])
                if current != f"{prio} {weight} {port} {value}":
                    to_print.append(line)
            if "  TXT " in line:
                domain, value = line.split(" TXT ")
                current = dns.get("TXT", domain.strip()[:-1])
                if domain.startswith("_mta-sts."):
                    if current.split("id=")[0] == value.split("id=")[0]:
                        continue
                if current != value:
                    to_print.append(line)
            if " IN TXT ( " in line:
                started_dkim_parsing = True
                dkim_lines = [line]
            if started_dkim_parsing and line.startswith('"'):
                dkim_lines.append(" " + line)
        domain, data = "\n".join(dkim_lines).split(" IN TXT ")
        current = dns.get("TXT", domain.strip()[:-1]).replace('" "', '"\n "')
        current = f"( {current} )"
        if current.replace(";", "\\;") != data:
            to_print.append(dkim_entry)

    if to_print:
        to_print.insert(
            0, "You should configure the following DNS entries at your provider:\n"
        )
        to_print.append(
            "\nIf you already configured the DNS entries, don't worry. It can take a while until they are public."
        )
        print("\n".join(to_print))
    else:
        out.green("Great! All your DNS entries are correct.")

    if not reverse_ipv4:
        print(
            f"\nYou should add a PTR/reverse DNS entry for {ipv4}, with the value: {args.config.mail_domain}"
        )
        print(
            "You can do so at your hosting provider (maybe this isn't your DNS provider)."
        )
    if not reverse_ipv6:
        print(
            f"\nYou should add a PTR/reverse DNS entry for {ipv6}, with the value: {args.config.mail_domain}"
        )
        print(
            "You can do so at your hosting provider (maybe this isn't your DNS provider)."
        )


def check_necessary_dns(args, out, msg, mail_domain):
    """Check whether $mail_domain and mta-sts.$mail_domain resolve.

    :param args: the argparse args object
    :param out: an object to control CLI output
    :param msg: a string like: "Now you should add %dnsentry% at your DNS provider:\n"
    :param mail_domain: the mail_domain of the chatmail server
    """
    dns = DNS(out, mail_domain)
    try:
        ipaddress = dns.resolve(mail_domain)
        mta_ipadress = dns.resolve("mta-sts." + mail_domain)
    except subprocess.CalledProcessError:
        ipaddress = None
        mta_ipadress = None
    entries = 0
    to_print = [msg]
    if not ipaddress:
        entries += 1
        to_print.append(f"\tA\t{mail_domain}.\t\t<your server's IPv4 address>")
    if not mta_ipadress or mta_ipadress != ipaddress:
        entries += 1
        to_print.append(f"\tCNAME\tmta-sts.{mail_domain}.\t{mail_domain}.")
    if entries == 1:
        singular = "this entry"
    elif entries == 2:
        singular = "these entries"
    else:
        return True
    to_print[0] = to_print[0].replace("%dnsentry%", singular)
    for line in to_print:
        print(line)
    print()
