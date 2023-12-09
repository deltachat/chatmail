from pathlib import Path
from fnmatch import fnmatch
import iniconfig


def read_config(inipath):
    cfg = iniconfig.IniConfig(inipath)
    return Config(inipath, params=cfg.sections["params"])


class Config:
    def __init__(self, inipath, params):
        self._inipath = inipath
        self.mailname = self.mail_domain = params["mailname"]
        self.max_user_send_per_minute = int(params["max_user_send_per_minute"])
        self.filtermail_smtp_port = int(params["filtermail_smtp_port"])
        self.postfix_reinject_port = int(params["postfix_reinject_port"])
        self.passthrough_recipients = params["passthrough_recipients"].split()
        self.privacy_postal = params.get("privacy_postal")
        self.privacy_mail = params.get("privacy_mail")
        self.privacy_pdo = params.get("privacy_pdo")
        self.privacy_supervisor = params.get("privacy_supervisor")

    def _getbytefile(self):
        return open(self._inipath, "rb")
