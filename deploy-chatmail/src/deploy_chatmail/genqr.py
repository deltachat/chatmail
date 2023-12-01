import importlib
import qrcode
import os
from PIL import ImageFont, ImageDraw, Image
import io


def gen_qr_png_data(maildomain):
    url = f"DCACCOUNT:https://{maildomain}/cgi-bin/newemail.py"
    image = gen_qr(maildomain, url)
    temp = io.BytesIO()
    image.save(temp, format="png")
    temp.seek(0)
    return temp


def gen_qr(maildomain, url):
    info = f"{maildomain} invite code"

    steps = (
        "1. Install https://get.delta.chat\n"
        "2. On setup screen scan above invite QR code\n"
        "3. Choose nickname & avatar\n"
        "+ chat with any e-mail address ...\n"
    )

    # load QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=1,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white")

    # paint all elements
    ttf_path = str(
        importlib.resources.files(__package__).joinpath("data/opensans-regular.ttf")
    )
    logo_red_path = str(
        importlib.resources.files(__package__).joinpath("data/delta-chat-bw.png")
    )

    assert os.path.exists(ttf_path), ttf_path
    font_size = 16
    font = ImageFont.truetype(font=ttf_path, size=font_size)

    num_lines = (info + steps).count("\n") + 3

    size = width = 384
    qr_padding = 6
    text_margin_right = 12
    text_height = font_size * num_lines
    height = size + text_height + qr_padding * 2

    image = Image.new("RGBA", (width, height), "white")

    draw = ImageDraw.Draw(image)

    qr_final_size = width - (qr_padding * 2)

    # draw text
    if hasattr(font, "getsize"):
        info_pos = (width - font.getsize(info.strip())[0]) // 2
    else:
        info_pos = (width - font.getbbox(info.strip())[3]) // 2

    draw.multiline_text(
        (info_pos, size - qr_padding // 2), info, font=font, fill="black", align="right"
    )
    draw.multiline_text(
        (text_margin_right, height - text_height + font_size * 1.0),
        steps,
        font=font,
        fill="black",
        align="left",
    )

    # paste QR code
    image.paste(
        qr_img.resize((qr_final_size, qr_final_size), resample=Image.NEAREST),
        (qr_padding, qr_padding),
    )

    # background delta logo
    logo2_img = Image.open(logo_red_path)
    logo2_width = int(size / 6)
    logo2 = logo2_img.resize((logo2_width, logo2_width), resample=Image.NEAREST)
    pos = int((size / 2) - (logo2_width / 2))
    image.paste(logo2, (pos, pos), mask=logo2)

    return image
