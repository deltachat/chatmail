import subprocess


def get_pass(filename: str) -> str:
    """Get the data from the password manager."""
    r = subprocess.run(["pass", "show", filename], capture_output=True, check=True)
    return r.stdout.decode("utf-8")

chatmail = [
    (
        "c1.testrun.org",
        {
            "ssh_user": "root",
            "domain": "c1.testrun.org",
            "dkim_selector": "2023",
            "dkim_key": get_pass("delta/c1.testrun.org/dkim_key"),
            "dkim_txt": get_pass("delta/c1.testrun.org/dkim_txt"),
        },
    ),
]
