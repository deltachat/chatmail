import os
from pyinfra import host, facts
from chatmail import deploy_chatmail


# the following is to prevent rate-limits with querying letsencrypt
# servers during deploys.  It probably makes more sense to check
# in acmetool if a cert exists and skip recreating it because
# the acmetool pyinfra will renew certs via its cronjob, anyway.

def unpack_acme_state():
    from pyinfra.operations import files, server
    from io import BytesIO

    local_acme_filename = "acme_state.tar.gz"

    if os.path.exists(local_acme_filename):
        with open(local_acme_filename, "rb") as f:
            acme_state = f.read()
        files.put(
            name="Upload acme state tar",
            src=BytesIO(acme_state),
            dest="/root/acme_state.tar.gz",
            mode="600",
        )
        server.shell(
            name="Unpack acme state directory",
            commands=[
                "mkdir -p /var/lib/acme && tar -C /var/lib/acme -x -z < /root/acme_state.tar.gz"
            ],
        )
    else:
        print("no cached acme state found, deploy will recreate letsencrypt certs")
        print("use this command to create a cache file:")
        ssh_host = f"{host.data.ssh_user}@{host.data.host.name}"
        cmd = f"'tar -C /var/lib/acme -c . -z' > {local_acme_filename}"
        print(f"ssh {ssh_host} {cmd}")


unpack_acme_state()

deploy_chatmail()
