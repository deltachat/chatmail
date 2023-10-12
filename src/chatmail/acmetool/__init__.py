from pathlib import Path

from pyinfra.operations import apt, files, systemd, server


def openfile(basename):
    # on newer python versions:
    # importlib.resources.files(__package__).joinpath(basename).open("rb")
    # but here we use a way supported on old pythons
    dirpath = Path(__path__[0])
    return dirpath.joinpath(basename).open("rb")


def deploy_acmetool(nginx_hook=False, email="", domains=[]):
    """Deploy acmetool."""
    apt.packages(
        name="Install acmetool",
        packages=["acmetool"],
    )

    files.put(
        src=openfile("acmetool.cron"),
        dest="/etc/cron.d/acmetool",
        user="root",
        group="root",
        mode="644",
    )

    if nginx_hook:
        files.put(
            src=openfile("acmetool.hook"),
            dest="/usr/lib/acme/hooks/nginx",
            user="root",
            group="root",
            mode="744",
        )

    files.template(
        src=openfile("response-file.yaml.j2"),
        dest="/var/lib/acme/conf/responses",
        user="root",
        group="root",
        mode="644",
        email=email,
    )

    service_file = files.put(
        src=openfile("acmetool-redirector.service"),
        dest="/etc/systemd/system/acmetool-redirector.service",
        user="root",
        group="root",
        mode="644",
    )
    systemd.service(
        name="Setup acmetool-redirector service",
        service="acmetool-redirector.service",
        running=True,
        enabled=True,
        restarted=service_file.changed,
    )

    for domain in domains:
        server.shell(
            name=f"Request certificate for {domain}",
            commands=[f"acmetool want {domain}"],
        )
