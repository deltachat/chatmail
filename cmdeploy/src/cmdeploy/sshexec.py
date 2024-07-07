import execnet


def exec_one_command(channel, cmd):
    # a pure function which executes on the remote ssh side
    # with the channel providing I/O
    import subprocess

    output = subprocess.check_output(cmd, shell=True).decode()
    channel.send(output)


def get_ip_addresses(channel):
    import socket

    res = []
    for typ in (socket.AF_INET, socket.AF_INET6):
        sock = socket.socket(typ, socket.SOCK_DGRAM)
        sock.settimeout(0)
        sock.connect(("notifications.delta.chat", 1))
        res.append(sock.getsockname()[0])

    channel.send(res)


class SSHExec:
    RemoteError = execnet.RemoteError

    def __init__(self, host, python="python3", timeout=60):
        target = host if "@" in host else f"root@{host}"
        self.gateway = execnet.makegateway(f"ssh={target}//python={python}")
        self.timeout = timeout

    def __call__(self, cmd, quiet=False):
        if not quiet:
            print(f"{self.gateway.spec.ssh} $ {cmd}")
        channel = self.gateway.remote_exec(exec_one_command, cmd=cmd)
        return channel.receive(timeout=self.timeout)

    def get_ip_addresses(self):
        channel = self.gateway.remote_exec(get_ip_addresses)
        return channel.receive(timeout=self.timeout)
