import execnet


def exec_one_command(channel, cmd):
    # this code executes on the remote ssh side
    # the channel can be used to send back results
    import subprocess

    output = subprocess.check_output(cmd, shell=True).decode()
    channel.send(output)


class SSHCommandExecutor:
    RemoteError = execnet.RemoteError

    def __init__(self, host, python="python3"):
        self.gateway = execnet.makegateway(f"ssh=root@{host}//python={python}")

    def shell_output(self, cmd, timeout=60):
        print(f"{self.gateway.spec.ssh} $ {cmd}")
        channel = self.gateway.remote_exec(exec_one_command, cmd=cmd)
        return channel.receive(timeout=timeout)
