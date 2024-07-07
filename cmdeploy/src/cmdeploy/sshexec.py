import execnet


class SSHExec:
    RemoteError = execnet.RemoteError

    def __init__(self, host, remote_funcs, python="python3", timeout=60):
        target = host if "@" in host else f"root@{host}"
        self.gateway = execnet.makegateway(f"ssh={target}//python={python}")
        self._remote_cmdloop_channel = self.gateway.remote_exec(remote_funcs)
        self.timeout = timeout

    def __call__(self, func, **kwargs):
        self._remote_cmdloop_channel.send((func.__name__, kwargs))
        return self._remote_cmdloop_channel.receive(timeout=self.timeout)
