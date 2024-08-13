import builtins
import importlib
import traceback

## Function Execution server


def _run_loop(cmd_channel):
    while cmd := cmd_channel.receive():
        cmd_channel.send(_handle_one_request(cmd))


def _handle_one_request(cmd):
    pymod_path, func_name, kwargs = cmd
    try:
        mod = importlib.import_module(pymod_path)
        func = getattr(mod, func_name)
        res = func(**kwargs)
        return ("finish", res)
    except:
        data = traceback.format_exc()
        return ("error", data)


def main(channel):
    # enable simple "print" logging

    builtins.print = lambda x="": channel.send(("log", x))

    _run_loop(channel)
