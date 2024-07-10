import sys

import execnet


class SSHExec:
    RemoteError = execnet.RemoteError

    def __init__(self, host, remote_funcs, verbose=False, python="python3", timeout=60):
        self.gateway = execnet.makegateway(f"ssh=root@{host}//python={python}")
        self._remote_cmdloop_channel = self.gateway.remote_exec(remote_funcs)
        self.timeout = timeout
        self.verbose = verbose

    def __call__(self, call, kwargs=None, log_callback=None):
        self._remote_cmdloop_channel.send((call.__name__, kwargs))
        while 1:
            code, data = self._remote_cmdloop_channel.receive(timeout=self.timeout)
            if log_callback is not None and code == "log":
                log_callback(data)
            elif code == "finish":
                return data

    def logged(self, call, kwargs):
        def log_progress(data):
            sys.stdout.write(".")
            sys.stdout.flush()

        title = call.__doc__
        if not title:
            title = call.__name__
        if self.verbose:
            print("[ssh] " + title)
            return self(call, kwargs, log_callback=print)
        else:
            print(title, end="")
            res = self(call, kwargs, log_callback=log_progress)
            print()
            return res
