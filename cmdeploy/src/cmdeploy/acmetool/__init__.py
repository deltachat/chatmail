import importlib.resources

from pyinfra import host
from pyinfra.facts.systemd import SystemdStatus
from pyinfra.operations import apt, files, server, systemd


def deploy_acmetool(email="", domains=[]):
    """Deploy acmetool."""
    apt.packages(
        name="Install acmetool",
        packages=["acmetool"],
    )

    files.put(
        src=importlib.resources.files(__package__).joinpath("acmetool.cron").open("rb"),
        dest="/etc/cron.d/acmetool",
        user="root",
        group="root",
        mode="644",
    )

    files.put(
        src=importlib.resources.files(__package__).joinpath("acmetool.hook").open("rb"),
        dest="/usr/lib/acme/hooks/nginx",
        user="root",
        group="root",
        mode="744",
    )

    files.template(
        src=importlib.resources.files(__package__).joinpath("response-file.yaml.j2"),
        dest="/var/lib/acme/conf/responses",
        user="root",
        group="root",
        mode="644",
        email=email,
    )

    files.template(
        src=importlib.resources.files(__package__).joinpath("target.yaml.j2"),
        dest="/var/lib/acme/conf/target",
        user="root",
        group="root",
        mode="644",
    )

    service_file = files.put(
        src=importlib.resources.files(__package__).joinpath(
            "acmetool-redirector.service"
        ),
        dest="/etc/systemd/system/acmetool-redirector.service",
        user="root",
        group="root",
        mode="644",
    )
    if host.get_fact(SystemdStatus).get("nginx.service"):
        systemd.service(
            name="Stop nginx service to free port 80",
            service="nginx",
            running=False,
        )

    systemd.service(
        name="Setup acmetool-redirector service",
        service="acmetool-redirector.service",
        running=True,
        enabled=True,
        restarted=service_file.changed,
    )

    server.shell(
        name=f"Request certificate for: {', '.join(domains)}",
        commands=[f"acmetool want --xlog.severity=debug {' '.join(domains)}"],
    )
