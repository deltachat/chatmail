import importlib.resources

from pyinfra.operations import apt, files, systemd, server


def deploy_acmetool(nginx_hook=False, email="", domains=[]):
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

    if nginx_hook:
        files.put(
            src=importlib.resources.files(__package__)
            .joinpath("acmetool.hook")
            .open("rb"),
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

    service_file = files.put(
        src=importlib.resources.files(__package__)
        .joinpath("acmetool-redirector.service")
        .open("rb"),
        dest="/etc/systemd/system/acmetool-redirector.service",
        user="root",
        group="root",
        mode="644",
    )
    systemd.service(
        name="Setup acmetool-redirector service",
        service="acmetool-redirector.service",
        running=False,
        enabled=False,
        restarted=service_file.changed,
    )

    for domain in domains:
        server.shell(
            name=f"Request certificate for {domain}",
            commands=[f"acmetool want {domain}"],
        )
