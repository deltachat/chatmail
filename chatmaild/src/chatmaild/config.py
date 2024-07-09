from pathlib import Path

import iniconfig


def read_config(inipath, mail_basedir=None):
    assert Path(inipath).exists(), inipath
    cfg = iniconfig.IniConfig(inipath)
    params = cfg.sections["params"]
    if mail_basedir is None:
        mail_basedir = Path(f"/home/vmail/mail/{params['mail_domain']}")
    return Config(inipath, params=params, mail_basedir=mail_basedir)


class Config:
    def __init__(self, inipath, params, mail_basedir: Path):
        self._inipath = inipath
        self.mail_domain = params["mail_domain"]
        self.max_user_send_per_minute = int(params["max_user_send_per_minute"])
        self.max_mailbox_size = params["max_mailbox_size"]
        self.delete_mails_after = params["delete_mails_after"]
        self.delete_inactive_users_after = int(params["delete_inactive_users_after"])
        self.username_min_length = int(params["username_min_length"])
        self.username_max_length = int(params["username_max_length"])
        self.password_min_length = int(params["password_min_length"])
        self.passthrough_senders = params["passthrough_senders"].split()
        self.passthrough_recipients = params["passthrough_recipients"].split()
        self.filtermail_smtp_port = int(params["filtermail_smtp_port"])
        self.postfix_reinject_port = int(params["postfix_reinject_port"])
        self.iroh_relay = params.get("iroh_relay")
        self.privacy_postal = params.get("privacy_postal")
        self.privacy_mail = params.get("privacy_mail")
        self.privacy_pdo = params.get("privacy_pdo")
        self.privacy_supervisor = params.get("privacy_supervisor")
        self.mail_basedir = mail_basedir

    def _getbytefile(self):
        return open(self._inipath, "rb")

    def get_user_maildir(self, addr):
        if addr and addr != "." and "/" not in addr:
            res = self.mail_basedir.joinpath(addr).resolve()
            if res.is_relative_to(self.mail_basedir):
                return res
        raise ValueError(f"invalid address {addr!r}")


def write_initial_config(inipath, mail_domain):
    from importlib.resources import files

    inidir = files(__package__).joinpath("ini")
    content = (
        inidir.joinpath("chatmail.ini.f").read_text().format(mail_domain=mail_domain)
    )
    if mail_domain.endswith(".testrun.org"):
        override_inipath = inidir.joinpath("override-testrun.ini")
        privacy = iniconfig.IniConfig(override_inipath)["privacy"]
        lines = []
        for line in content.split("\n"):
            for key, value in privacy.items():
                value_lines = value.strip().split("\n")
                if not line.startswith(f"{key} =") or not value_lines:
                    continue
                if len(value_lines) == 1:
                    lines.append(f"{key} = {value}")
                else:
                    lines.append(f"{key} =")
                    for vl in value_lines:
                        lines.append(f"    {vl}")
                break
            else:
                lines.append(line)
        content = "\n".join(lines)

    inipath.write_text(content)
