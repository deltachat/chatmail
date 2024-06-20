import iniconfig


def read_config(inipath):
    cfg = iniconfig.IniConfig(inipath)
    return Config(inipath, params=cfg.sections["params"])


class Config:
    def __init__(self, inipath, params):
        self._inipath = inipath
        self.mail_domain = params["mail_domain"]
        self.max_user_send_per_minute = int(params["max_user_send_per_minute"])
        self.max_mailbox_size = params["max_mailbox_size"]
        self.delete_mails_after = params["delete_mails_after"]
        self.username_min_length = int(params["username_min_length"])
        self.username_max_length = int(params["username_max_length"])
        self.password_min_length = int(params["password_min_length"])
        self.passthrough_senders = params["passthrough_senders"].split()
        self.passthrough_recipients = params["passthrough_recipients"].split()
        self.filtermail_smtp_port = int(params["filtermail_smtp_port"])
        self.postfix_reinject_port = int(params["postfix_reinject_port"])
        self.disable_ipv6 = True if params.get("disable_ipv6") == "True" else False
        self.iroh_relay = params.get("iroh_relay")
        self.privacy_postal = params.get("privacy_postal")
        self.privacy_mail = params.get("privacy_mail")
        self.privacy_pdo = params.get("privacy_pdo")
        self.privacy_supervisor = params.get("privacy_supervisor")

    def _getbytefile(self):
        return open(self._inipath, "rb")


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
