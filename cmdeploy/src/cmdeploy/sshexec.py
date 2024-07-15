import sys

import execnet


class FuncError(Exception):
    pass


def print_stderr(item="", end="\n"):
    print(item, file=sys.stderr, end=end)


class SSHExec:
    RemoteError = execnet.RemoteError
    FuncError = FuncError

    def __init__(self, host, remote_funcs, verbose=False, python="python3", timeout=60):
        self.gateway = execnet.makegateway(f"ssh=root@{host}//python={python}")
        self._remote_cmdloop_channel = self.gateway.remote_exec(remote_funcs)
        self.timeout = timeout
        self.verbose = verbose

    def __call__(self, call, kwargs=None, log_callback=None):
        if kwargs is None:
            kwargs = {}
        self._remote_cmdloop_channel.send((call.__name__, kwargs))
        while 1:
            code, data = self._remote_cmdloop_channel.receive(timeout=self.timeout)
            if log_callback is not None and code == "log":
                log_callback(data)
            elif code == "finish":
                return data
            elif code == "error":
                raise self.FuncError(data)

    def logged(self, call, kwargs):
        def log_progress(data):
            sys.stderr.write(".")
            sys.stderr.flush()

        title = call.__doc__
        if not title:
            title = call.__name__
        if self.verbose:
            print_stderr("[ssh] " + title)
            return self(call, kwargs, log_callback=print_stderr)
        else:
            print_stderr(title, end="")
            res = self(call, kwargs, log_callback=log_progress)
            print_stderr()
            return res
