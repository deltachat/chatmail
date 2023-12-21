import requests

from cmdeploy.genqr import gen_qr_png_data


def test_gen_qr_png_data(maildomain):
    data = gen_qr_png_data(maildomain)
    assert data


def test_fastcgi_working(maildomain, chatmail_config):
    url = f"https://{maildomain}/cgi-bin/newemail.py"
    print(url)
    res = requests.post(url)
    assert maildomain in res.json().get("email")
    assert len(res.json().get("password")) > chatmail_config.password_min_length


def test_newemail_configure(maildomain, rpc):
    """Test configuring accounts by scanning a QR code works."""
    url = f"DCACCOUNT:https://{maildomain}/cgi-bin/newemail.py"
    for i in range(3):
        account_id = rpc.add_account()
        rpc.set_config_from_qr(account_id, url)
        rpc.configure(account_id)
