"""

The 'cmdeploy.remote' sub package contains modules with remotely executing functions.

Its "_sshexec_bootstrap" module is executed remotely through `SSHExec`
and its main() loop there stays connected via a command channel,
ready to receive function invocations ("command") and return results.
"""

from . import rdns, rshell

__all__ = ["rdns", "rshell"]
