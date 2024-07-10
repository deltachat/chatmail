from pathlib import Path

import iniconfig


def read_config(inipath):
    assert Path(inipath).exists(), inipath
    cfg = iniconfig.IniConfig(inipath)
    params = cfg.sections["params"]
    return Config(inipath, params=params)


class Config:
    def __init__(self, inipath, params):
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
        self.mailboxes_dir = Path(params["mailboxes_dir"].strip())
        self.passdb_path = params["passdb_path"].strip().rstrip("/")
        self.filtermail_smtp_port = int(params["filtermail_smtp_port"])
        self.postfix_reinject_port = int(params["postfix_reinject_port"])
        self.iroh_relay = params.get("iroh_relay")
        self.privacy_postal = params.get("privacy_postal")
        self.privacy_mail = params.get("privacy_mail")
        self.privacy_pdo = params.get("privacy_pdo")
        self.privacy_supervisor = params.get("privacy_supervisor")

    def _getbytefile(self):
        return open(self._inipath, "rb")

    def get_user_maildir(self, addr):
        if addr and addr != "." and "/" not in addr:
            res = self.mailboxes_dir.joinpath(addr).resolve()
            if res.is_relative_to(self.mailboxes_dir):
                return res
        raise ValueError(f"invalid address {addr!r}")


def write_initial_config(inipath, mail_domain, overrides):
    """Write out default config file, using the specified config value overrides."""
    from importlib.resources import files

    inidir = files(__package__).joinpath("ini")
    source_inipath = inidir.joinpath("chatmail.ini.f")
    content = source_inipath.read_text().format(mail_domain=mail_domain)

    # apply config overrides
    new_lines = []
    for line in content.split("\n"):
        new_line = line.strip()
        if new_line and new_line[0] not in "#[":
            name, value = map(str.strip, new_line.split("=", maxsplit=1))
            value = overrides.get(name, value)
            new_line = f"{name} = {value}"
        new_lines.append(new_line)

    content = "\n".join(new_lines)

    # apply testrun privacy overrides

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
