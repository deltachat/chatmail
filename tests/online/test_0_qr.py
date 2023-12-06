

from deploy_chatmail.genqr import gen_qr_png_data


def test_gen_qr_png_data(maildomain):
    data = gen_qr_png_data(maildomain)
    assert data
