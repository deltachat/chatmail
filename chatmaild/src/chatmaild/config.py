
from fnmatch import fnmatch
import iniconfig


class Config:
    def __init__(self, mailname, section):
        self.mailname = mailname
        self.privacy_postal = section.get("privacy_postal")
        self.privacy_mail = section.get("privacy_mail")
        self.privacy_pdo = section.get("privacy_pdo")
        self.privacy_supervisor = section.get("privacy_supervisor")
        self.has_privacy_policy = self.privacy_mail != None


def read_config(inipath, mailname):
    ini = iniconfig.IniConfig(inipath)
    privacy = None
    for section in ini:
        if section.name.startswith("privacy:"):
            domain = section["domain"]
            if fnmatch(mailname, domain):
                privacy = section
                break

    return Config(mailname, privacy or {})
