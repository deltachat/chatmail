from subprocess import CalledProcessError as ShellError
from subprocess import check_output


def shell(command, fail_ok=False):
    print(f"$ {command}")
    try:
        return check_output(command, shell=True).decode().rstrip()
    except ShellError:
        if not fail_ok:
            raise
        return ""


def get_systemd_running():
    lines = shell("systemctl --type=service --state=running").split("\n")
    return [line for line in lines if line.startswith("  ")]
