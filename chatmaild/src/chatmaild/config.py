

from pathlib import Path
from fnmatch import fnmatch
import iniconfig

system_mailname_path = Path("/etc/mailname")


def read_config(inipath, mailname=None):
    if mailname is None:
        with open(system_mailname_path) as f:
            mailname = f.read().strip()

    ini = iniconfig.IniConfig(inipath)
    privacy = {}
    for section in ini:
        if section.name.startswith("privacy:"):
            domain = section["domain"]
            if fnmatch(mailname, domain):
                privacy = section
                break

    return Config(inipath, mailname, privacy, params=ini.sections["params"])


class Config:
    def __init__(self, inipath, mailname, privacy, params):
        self._inipath = inipath
        self.mailname = mailname
        self.privacy_postal = privacy.get("privacy_postal")
        self.privacy_mail = privacy.get("privacy_mail")
        self.privacy_pdo = privacy.get("privacy_pdo")
        self.privacy_supervisor = privacy.get("privacy_supervisor")
        self.max_user_send_per_minute = int(params["max_user_send_per_minute"])
        self.filtermail_smtp_port = int(params["filtermail_smtp_port"])
        self.postfix_reinject_port = int(params["postfix_reinject_port"])

    def _getbytefile(self):
        return open(self._inipath, "rb")
