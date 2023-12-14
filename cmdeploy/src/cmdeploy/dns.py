import requests
from ipaddress import ip_address


class DNS:
    def __init__(self, out, mail_domain):
        self.session = requests.Session()
        self.out = out
        self.ssh = f"ssh root@{mail_domain}"
        self.out.shell_output(f"{self.ssh} -- unbound-control flush {mail_domain}")

    def get_ipv4(self):
        cmd = "ip a | grep 'inet ' | grep 'scope global' | grep -oE '[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}' | head -1"
        return self.out.shell_output(f"{self.ssh} -- {cmd}").strip()

    def get_ipv6(self):
        cmd = "ip a | grep inet6 | grep 'scope global' | sed -e 's#/64 scope global##' | sed -e 's#inet6##'"
        return self.out.shell_output(f"{self.ssh} -- {cmd}").strip()

    def get(self, typ: str, domain: str) -> str:
        """Get a DNS entry"""
        dig_result = self.out.shell_output(f"{self.ssh} -- dig {typ} {domain}")
        line_num = 0
        for line in dig_result.splitlines():
            line_num += 1
            if line.strip() == ";; ANSWER SECTION:":
                return dig_result.splitlines()[line_num].split("\t")[-1]

    def resolve(self, domain: str) -> str:
        result = self.get("A", domain)
        if not result:
            result = self.get("CNAME", domain)
            if result:
                result = self.get("A", result[:-1])
                if not result:
                    result = self.get("AAAA", domain)
        return result

    def check_ptr_record(self, ip: str, mail_domain) -> str:
        """Check the PTR record for an IPv4 or IPv6 address."""
        result = self.get("PTR", ip_address(ip).reverse_pointer)
        return result[:-1] == mail_domain
