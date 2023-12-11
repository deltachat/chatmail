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
