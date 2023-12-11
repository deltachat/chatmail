"""
Provides the `cmdeploy` entry point function,
along with command line option and subcommand parsing.
"""
import argparse
import datetime
import shutil
import subprocess
import importlib
import os
import sys
from pathlib import Path


from termcolor import colored
from chatmaild.config import read_config, write_initial_config


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
        out.red(f"Path exists, not modifying: {args.inipath}")
        raise SystemExit(1)
    write_initial_config(args.inipath, args.chatmail_domain)
    out.green(f"created config file for {args.chatmail_domain} in {args.inipath}")


def run_cmd_options(parser):
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="don't actually modify the server",
    )


def run_cmd(args, out):
    """Deploy chatmail services on the remote server."""

    popen_args = ["pyinfra"]
    if args.dry_run:
        popen_args.append("--dry")
    popen_args.extend(["--ssh-user", "root", args.config.mailname])
    popen_args.append("deploy-chatmail/src/deploy_chatmail/deploy.py")

    out(f"{os.getcwd()} $ {' '.join(popen_args)}")
    env = os.environ.copy()
    env["CHATMAIL_DOMAIN"] = args.config.mailname
    subprocess.check_call(popen_args, env=env)


def dns_cmd(args, out):
    """Generate dns zone file."""
    template = importlib.resources.files(__package__).joinpath("chatmail.zone.f")
    ssh = f"ssh root@{args.config.mailname}"

    def shell_output(arg):
        out(f"[{arg}]", file=sys.stderr)
        return subprocess.check_output(arg, shell=True).decode()

    def read_dkim_entries(entry):
        lines = []
        for line in entry.split("\n"):
            if line.startswith(";") or not line.strip():
                continue
            line = line.replace("\t", " ")
            lines.append(line)
        return "\n".join(lines)

    acme_account_url = shell_output(f"{ssh} -- acmetool account-url")
    dkim_entry = read_dkim_entries(shell_output(f"{ssh} -- opendkim-genzone -F"))

    out(
        f"[writing {args.config.mailname} zone data (using space as separator) to stdout output]",
        green=True,
    )
    print(
        template.read_text()
        .format(
            acme_account_url=acme_account_url,
            email=f"root@{args.config.mailname}",
            sts_id=datetime.datetime.now().strftime("%Y%m%d%H%M"),
            chatmail_domain=args.config.mailname,
            dkim_entry=dkim_entry,
        )
        .strip()
    )


def status_cmd(args, out):
    """Display status for online chatmail instance."""

    ssh = f"ssh root@{args.config.mailname}"

    def shell_output(arg):
        return subprocess.check_output(arg, shell=True).decode()

    out.green(f"chatmail domain: {args.config.mailname}")
    if args.config.privacy_mail:
        out.green("privacy settings: present")
    else:
        out.red("no privacy settings")

    out(f"[retrieving info by invoking {ssh}]", file=sys.stderr)

    s1 = "systemctl --type=service --state=running"
    for line in shell_output(f"{ssh} -- {s1}").split("\n"):
        if line.startswith("  "):
            print(line)


def test_cmd(args, out):
    """Run local and online tests."""

    tox = shutil.which("tox")
    proc1 = subprocess.run([tox, "-c", "chatmaild"])
    proc2 = subprocess.run([tox, "-c", "deploy-chatmail"])

    pytest_path = shutil.which("pytest")
    proc3 = subprocess.run(
        [pytest_path, "tests/online", "-rs", "-x", "-vrx", "--durations=5"]
    )
    if any(x.returncode != 0 for x in (proc1, proc2, proc3)):
        return 1
    return 0


def bench_cmd(args, out):
    """Run benchmarks against an online chatmail instance."""
    pytest_path = shutil.which("pytest")
    benchmark = "tests/online/benchmark.py"
    subprocess.check_call([pytest_path, benchmark, "-vrx"])


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
    doc = func.__doc__.strip().strip(".")
    p = subparsers.add_parser(name, description=doc, help=doc)
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
    if args.func.__name__ != "init_cmd":
        if not args.inipath.exists():
            out.red(f"expecting {args.inipath} to exist, run init first?")
            raise SystemExit(1)
        try:
            args.config = read_config(args.inipath)
        except Exception as ex:
            out.red(ex)
            raise SystemExit(1)

    try:
        sys.exit(args.func(args, out, **kwargs))
    except KeyboardInterrupt:
        out.red("KeyboardInterrupt")
        sys.exit(130)


if __name__ == "__main__":
    main()
