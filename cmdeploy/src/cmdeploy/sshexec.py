import execnet


def exec_one_command(channel, cmd):
    # a pure function which executes on the remote ssh side
    # with the channel providing I/O
    import subprocess

    output = subprocess.check_output(cmd, shell=True).decode()
    channel.send(output)


class SSHExec:
    RemoteError = execnet.RemoteError

    def __init__(self, host, python="python3"):
        target = host if "@" in host else f"root@{host}"
        self.gateway = execnet.makegateway(f"ssh={target}//python={python}")

    def __call__(self, cmd, timeout=60, quiet=False):
        if not quiet:
            print(f"{self.gateway.spec.ssh} $ {cmd}")
        channel = self.gateway.remote_exec(exec_one_command, cmd=cmd)
        return channel.receive(timeout=timeout)
