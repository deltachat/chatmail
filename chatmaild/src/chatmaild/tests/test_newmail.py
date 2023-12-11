import json

import chatmaild
from chatmaild.newemail import create_newemail_dict, print_new_account


def test_create_newemail_dict():
    ac1 = create_newemail_dict(domain="example.org")
    assert "@" in ac1["email"]
    assert len(ac1["password"]) >= 10

    ac2 = create_newemail_dict(domain="example.org")

    assert ac1["email"] != ac2["email"]
    assert ac1["password"] != ac2["password"]


def test_print_new_account(capsys, monkeypatch, maildomain, tmpdir):
    p = tmpdir.join("mailname")
    p.write(maildomain)
    monkeypatch.setattr(chatmaild.newemail, "mail_domain_path", str(p))
    print_new_account()
    out, err = capsys.readouterr()
    lines = out.split("\n")
    assert lines[0] == "Content-Type: application/json"
    assert not lines[1]
    dic = json.loads(lines[2])
    assert dic["email"].endswith(f"@{maildomain}")
    assert len(dic["password"]) >= 10
