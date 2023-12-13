"""
Provides the `cmdeploy` entry point function,
along with command line option and subcommand parsing.
"""
import argparse
import datetime
import shutil
import subprocess
import importlib.resources
import importlib.util
import os
import sys
from pathlib import Path


from termcolor import colored
from chatmaild.config import read_config, write_initial_config
from cmdeploy.dns import DNS


#
# cmdeploy sub commands and options
#


def init_cmd_options(parser):
    parser.add_argument(
        "chatmail_domain",
        action="store",
        help="fully qualified DNS domain name for your chatmail instance",
    )


def init_cmd(args, out):
    """Initialize chatmail config file."""
    if args.inipath.exists():
        print(f"Path exists, not modifying: {args.inipath}")
    else:
        write_initial_config(args.inipath, args.chatmail_domain)
        out.green(f"created config file for {args.chatmail_domain} in {args.inipath}")
    dns = DNS()
    ipaddress = dns.resolve(args.chatmail_domain)
    mta_ipadress = dns.resolve("mta-sts." + args.chatmail_domain)
    entries = 0
    to_print = ["Now you should add %dnsentry% at your DNS provider:\n"]
    if not ipaddress:
        entries += 1
        to_print.append(f"\tA\t{args.chatmail_domain}.\t\t<your server's IPv4 address>")
    if not mta_ipadress or mta_ipadress != ipaddress:
        entries += 1
        to_print.append(
            f"\tCNAME\tmta-sts.{args.chatmail_domain}.\t{args.chatmail_domain}."
        )
    if entries == 1:
        singular = "this entry"
    elif entries == 2:
        singular = "these entries"
    else:
        return
    to_print[0] = to_print[0].replace("%dnsentry%", singular)
    for line in to_print:
        print(line)
    print()


def run_cmd_options(parser):
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="don't actually modify the server",
    )


def run_cmd(args, out):
    """Deploy chatmail services on the remote server."""

    env = os.environ.copy()
    env["CHATMAIL_INI"] = args.inipath
    deploy_path = importlib.resources.files(__package__).joinpath("deploy.py").resolve()
    pyinf = "pyinfra --dry" if args.dry_run else "pyinfra"
    cmd = f"{pyinf} --ssh-user root {args.config.mail_domain} {deploy_path}"

    mail_domain = args.config.mail_domain
    dns = DNS()
    root_ip = dns.resolve(mail_domain)
    mta_ip = dns.resolve(f"mta-sts.{mail_domain}")
    if not root_ip or root_ip != mta_ip:
        out.red("DNS entries missing. Show instructions with:\n")
        print(f"\tcmdeploy init {mail_domain}\n")
        sys.exit(1)
    out.check_call(cmd, env=env)


def dns_cmd_options(parser):
    parser.add_argument(
        "--zonefile",
        dest="zonefile",
        help="print the whole zonefile for deploying directly",
    )


def dns_cmd(args, out):
    """Generate dns zone file."""
    template = importlib.resources.files(__package__).joinpath("chatmail.zone.f")
    ssh = f"ssh root@{args.config.mail_domain}"
    get_ipv6 = "ip a | grep inet6 | grep 'scope global' | sed -e 's#/64 scope global##' | sed -e 's#inet6##'"
    get_ipv4 = "ip a | grep 'inet ' | grep 'scope global' | grep -oE '[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}' | head -1"
    dns = DNS()

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
    ipv6 = out.shell_output(f"{ssh} -- {get_ipv6}").strip()
    ipv4 = out.shell_output(f"{ssh} -- {get_ipv4}").strip()

    print()
    if not dns.check_ptr_record(ipv4, args.config.mail_domain):
        print(
            f"You should add a PTR/reverse DNS entry for {ipv4}, with the value: {args.config.mail_domain}"
        )
        print(
            "You can do so at your hosting provider (maybe this isn't your DNS provider).\n"
        )
    if not dns.check_ptr_record(ipv6, args.config.mail_domain):
        print(
            f"You should add a PTR/reverse DNS entry for {ipv6}, with the value: {args.config.mail_domain}"
        )
        print(
            "You can do so at your hosting provider (maybe this isn't your DNS provider).\n"
        )

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
                    if current != value:
                        to_print.append(line)
            if " MX " in line:
                domain, typ, prio, value = line.split()
                current = dns.resolve_mx(domain[:-1])
                if not current[0]:
                    to_print.append(line)
                elif current[1] != value:
                    print(line.replace(prio, str(current[0] + 1)))
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


def status_cmd(args, out):
    """Display status for online chatmail instance."""

    ssh = f"ssh root@{args.config.mail_domain}"

    out.green(f"chatmail domain: {args.config.mail_domain}")
    if args.config.privacy_mail:
        out.green("privacy settings: present")
    else:
        out.red("no privacy settings")

    s1 = "systemctl --type=service --state=running"
    for line in out.shell_output(f"{ssh} -- {s1}").split("\n"):
        if line.startswith("  "):
            print(line)


def test_cmd_options(parser):
    parser.add_argument(
        "--slow",
        dest="slow",
        action="store_true",
        help="also run slow tests",
    )


def test_cmd(args, out):
    """Run local and online tests for chatmail deployment.

    This will automatically pip-install 'deltachat' if it's not available.
    """

    x = importlib.util.find_spec("deltachat")
    if x is None:
        out.check_call(f"{sys.executable} -m pip install deltachat")

    pytest_path = shutil.which("pytest")
    pytest_args = [
        pytest_path,
        "cmdeploy/src/",
        "-n4",
        "-rs",
        "-x",
        "-vrx",
        "--durations=5",
    ]
    if args.slow:
        pytest_args.append("--slow")
    ret = out.run_ret(pytest_args)
    return ret


def fmt_cmd_options(parser):
    parser.add_argument(
        "--verbose",
        "-v",
        dest="verbose",
        action="store_true",
        help="provide information on invocations",
    )

    parser.add_argument(
        "--check",
        "-c",
        action="store_true",
        help="only check but don't fix problems",
    )


def fmt_cmd(args, out):
    """Run formattting fixes (ruff and black) on all chatmail source code."""

    sources = [str(importlib.resources.files(x)) for x in ("chatmaild", "cmdeploy")]
    black_args = [shutil.which("black")]
    ruff_args = [shutil.which("ruff")]

    if args.check:
        black_args.append("--check")
    else:
        ruff_args.append("--fix")

    if not args.verbose:
        black_args.append("-q")
        ruff_args.append("-q")

    black_args.extend(sources)
    ruff_args.extend(sources)

    out.check_call(" ".join(black_args), quiet=not args.verbose)
    out.check_call(" ".join(ruff_args), quiet=not args.verbose)
    return 0


def bench_cmd(args, out):
    """Run benchmarks against an online chatmail instance."""
    args = ["pytest", "--pyargs", "cmdeploy.tests.online.benchmark", "-vrx"]
    cmdstring = " ".join(args)
    out.green(f"[$ {cmdstring}]")
    subprocess.check_call(args)


def webdev_cmd(args, out):
    """Run local web development loop for static web pages."""
    from .www import main

    main()


#
# Parsing command line options and starting commands
#


class Out:
    """Convenience output printer providing coloring."""

    def red(self, msg, file=sys.stderr):
        print(colored(msg, "red"), file=file)

    def green(self, msg, file=sys.stderr):
        print(colored(msg, "green"), file=file)

    def __call__(self, msg, red=False, green=False, file=sys.stdout):
        color = "red" if red else ("green" if green else None)
        print(colored(msg, color), file=file)

    def shell_output(self, arg):
        self(f"[$ {arg}]", file=sys.stderr)
        return subprocess.check_output(arg, shell=True).decode()

    def check_call(self, arg, env=None, quiet=False):
        if not quiet:
            self(f"[$ {arg}]", file=sys.stderr)
        return subprocess.check_call(arg, shell=True, env=env)

    def run_ret(self, args, env=None, quiet=False):
        if not quiet:
            cmdstring = " ".join(args)
            self(f"[$ {cmdstring}]", file=sys.stderr)
        proc = subprocess.run(args, env=env)
        return proc.returncode


def add_config_option(parser):
    parser.add_argument(
        "--config",
        dest="inipath",
        action="store",
        default=Path("chatmail.ini"),
        type=Path,
        help="path to the chatmail.ini file",
    )


def add_subcommand(subparsers, func):
    name = func.__name__
    assert name.endswith("_cmd")
    name = name[:-4]
    doc = func.__doc__.strip()
    help = doc.split("\n")[0].strip(".")
    p = subparsers.add_parser(name, description=doc, help=help)
    p.set_defaults(func=func)
    add_config_option(p)
    return p


description = """
Setup your chatmail server configuration and
deploy it via SSH to your remote location.
"""


def get_parser():
    """Return an ArgumentParser for the 'cmdeploy' CLI"""

    parser = argparse.ArgumentParser(description=description.strip())
    subparsers = parser.add_subparsers(title="subcommands")

    # find all subcommands in the module namespace
    glob = globals()
    for name, func in glob.items():
        if name.endswith("_cmd"):
            subparser = add_subcommand(subparsers, func)
            addopts = glob.get(name + "_options")
            if addopts is not None:
                addopts(subparser)

    return parser


def main(args=None):
    """Provide main entry point for 'xdcget' CLI invocation."""
    parser = get_parser()
    args = parser.parse_args(args=args)
    if not hasattr(args, "func"):
        return parser.parse_args(["-h"])
    out = Out()
    kwargs = {}
    if args.func.__name__ not in ("init_cmd", "fmt_cmd"):
        if not args.inipath.exists():
            out.red(f"expecting {args.inipath} to exist, run init first?")
            raise SystemExit(1)
        try:
            args.config = read_config(args.inipath)
        except Exception as ex:
            out.red(ex)
            raise SystemExit(1)

    try:
        res = args.func(args, out, **kwargs)
        if res is None:
            res = 0
        return res

    except KeyboardInterrupt:
        out.red("KeyboardInterrupt")
        sys.exit(130)


if __name__ == "__main__":
    main()
