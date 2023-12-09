"""
Provides the `cmdeploy` entry point function,
along with command line option and subcommand parsing.
"""
import importlib.resources
import argparse
import subprocess
import os
from pathlib import Path

import iniconfig

from termcolor import colored
from chatmaild.config import read_config


class Out:
    """Convenience print output printer providing coloring."""

    def red(self, msg):
        print(colored(msg, "red"))

    def green(self, msg):
        print(colored(msg, "green"))

    def __call__(self, msg, red=False, green=False):
        color = "red" if red else ("green" if green else None)
        print(colored(msg, color))


description = """\
Setup your chatmail server configuration and
deploy it via SSH to your remote location.
"""


def add_config_option(parser):
    parser.add_argument(
        "--config",
        dest="chatmail_ini",
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
    p = subparsers.add_parser(name, description=doc, help=doc)
    p.set_defaults(func=func)
    return p


def get_parser():
    """Return an ArgumentParser for the 'cmdeploy' CLI."""
    parser = argparse.ArgumentParser(description=description)
    subparsers = parser.add_subparsers(
        title="subcommands",
    )

    init_parser = add_subcommand(subparsers, init_cmd)
    add_config_option(init_parser)
    init_parser.add_argument(
        "chatmail_domain",
        action="store",
        help="fully qualified DNS domain name for your chatmail instance",
    )

    install_parser = add_subcommand(subparsers, install_cmd)
    add_config_option(install_parser)
    install_parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        help="don't actually modify the server",
    )

    add_subcommand(subparsers, webdev_cmd)
    return parser


def write_initial_config(inipath, mailname, out):
    inidir = importlib.resources.files(__package__).joinpath("ini")
    content = inidir.joinpath("chatmail.ini.f").read_text().format(mailname=mailname)
    if mailname.endswith(".testrun.org"):
        override_inipath = inidir.joinpath("override-testrun.ini")
        privacy = iniconfig.IniConfig(override_inipath)["privacy"]
        lines = []
        for line in content.split("\n"):
            for key, value in privacy.items():
                value_lines = value.strip().split("\n")
                if not line.startswith(f"{key} =") or not value_lines:
                    continue
                if len(value_lines) == 1:
                    lines.append(f"{key} = {value}")
                else:
                    lines.append(f"{key} =")
                    for vl in value_lines:
                        lines.append(f"    {vl}")
                break
            else:
                lines.append(line)
        content = "\n".join(lines)

    inipath.write_text(content)
    out(f"written {inipath} for chatmail domain {mailname}")


def init_cmd(args, out):
    """Initialize chatmail config file."""
    if args.chatmail_ini.exists():
        out.red(f"Path exists, not modifying: {args.chatmail_ini}")
        raise SystemExit(1)
    write_initial_config(args.chatmail_ini, args.chatmail_domain, out)


def install_cmd(args, out):
    """Install or update chatmail services on the remote server."""
    import pyinfra

    try:
        config = read_config(args.chatmail_ini)
    except Exception as ex:
        out.red(ex)
        raise SystemExit(1)

    popen_args = ["pyinfra"]
    if args.dry_run:
        popen_args.append("--dry")
    popen_args.extend(["--ssh-user", "root", config.mailname])
    popen_args.append("deploy-chatmail/src/deploy_chatmail/deploy.py")

    out(f"{os.getcwd()} $ {' '.join(popen_args)}")
    env = os.environ.copy()
    env["CHATMAIL_DOMAIN"] = config.mailname
    subprocess.check_call(popen_args, env=env)


def webdev_cmd(args, out):
    """Run web development loop for static local web pages."""
    from .www import main

    main()


def main(args=None):
    """Provide main entry point for 'xdcget' CLI invocation."""
    parser = get_parser()
    args = parser.parse_args(args=args)
    if not hasattr(args, "func"):
        return parser.parse_args(["-h"])
    out = Out()
    args.func(args, out)


if __name__ == "__main__":
    main()
