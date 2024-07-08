import execnet


class SSHExec:
    RemoteError = execnet.RemoteError

    def __init__(self, host, remote_funcs, log=None, python="python3", timeout=60):
        self.ssh_target = host if "@" in host else f"root@{host}"
        self.gateway = execnet.makegateway(f"ssh={self.ssh_target}//python={python}")
        self._remote_cmdloop_channel = self.gateway.remote_exec(remote_funcs)
        self.log = log
        self.timeout = timeout

    def __call__(self, func, **kwargs):
        self._remote_cmdloop_channel.send((func.__name__, kwargs))
        while 1:
            code, data = self._remote_cmdloop_channel.receive(timeout=self.timeout)
            if code == "log" and self.log:
                self.log(data)
            elif code == "finish":
                return data
