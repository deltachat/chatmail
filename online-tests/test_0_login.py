import pytest
import smtplib


def test_login_basic_functioning(imap_or_smtp, gencreds, lp):
    """Test a) that an initial login creates a user automatically
    and b) verify we can also login a second time with the same password
    and c) that using a different password fails the login."""
    user, password = gencreds()
    lp.sec(f"login first time with {user} {password}")
    imap_or_smtp.connect()
    imap_or_smtp.login(user, password)
    lp.indent("success")

    lp.sec(f"reconnect and login second time {user} {password}")
    imap_or_smtp.connect()
    imap_or_smtp.login(user, password)
    imap_or_smtp.connect()
    lp.sec("success")

    lp.sec(f"reconnect and verify wrong password fails {user} ")
    imap_or_smtp.connect()
    with pytest.raises(imap_or_smtp.AuthError):
        imap_or_smtp.login(user, password + "wrong")


def test_login_same_password(imap_or_smtp, gencreds):
    """Test two different users logging in with the same password
    to ensure that authentication process does not confuse the users
    by using only the password hash as a key.
    """
    user1, password1 = gencreds()
    user2, _ = gencreds()
    imap_or_smtp.connect()
    imap_or_smtp.login(user1, password1)
    imap_or_smtp.connect()
    imap_or_smtp.login(user2, password1)


def test_exceed_rate_limit(smtp, gencreds):
    """Test that the outbound rate limit is exceeded if we send a lot of messages at once."""
    user, password = gencreds()
    smtp.connect()
    smtp.login(user, password)

    to_addr = "foobar@example.org"
    mail = "\r\n".join(
        [
            "Subject: ...",
            f"From: <{user}>",
            f"To: <{to_addr}>",
            "Date: Sun, 15 Oct 2023 16:43:21 +0000",
            "Message-ID: <Mr.UVyJWZmkCKM.hGzNc6glBE_@c2.testrun.org>",
            "In-Reply-To: <Mr.MvmCz-GQbi_.6FGRkhDf05c@c2.testrun.org>",
            "References: <Mr.3gckbNy5bch.uK3Hd2Ws6-w@c2.testrun.org>",
            "\t<Mr.MvmCz-GQbi_.6FGRkhDf05c@c2.testrun.org>",
            "Chat-Version: 1.0",
            f"Autocrypt: addr={user}; prefer-encrypt=mutual;",
            "\tkeydata=xjMEZSwWjhYJKwYBBAHaRw8BAQdAQBEhqeJh0GueHB6kF/DUQqYCxARNBVokg/AzT+7LqH",
            "\trNFzxiYXJiYXpAYzIudGVzdHJ1bi5vcmc+wosEEBYIADMCGQEFAmUsFo4CGwMECwkIBwYVCAkKCwID",
            "\tFgIBFiEEFTfUNvVnY3b9F7yHnmme1PfUhX8ACgkQnmme1PfUhX9A4AEAnHWHp49eBCMHK5t66gYPiW",
            "\tXQuB1mwUjzGfYWB+0RXUoA/0xcQ3FbUNlGKW7Blp6eMFfViv6Mv2d3kNSXACB6nmcMzjgEZSwWjhIK",
            "\tKwYBBAGXVQEFAQEHQBpY5L2M1XHo0uxf8SX1wNLBp/OVvidoWHQF2Jz+kJsUAwEIB8J4BBgWCAAgBQ",
            "\tJlLBaOAhsMFiEEFTfUNvVnY3b9F7yHnmme1PfUhX8ACgkQnmme1PfUhX/INgEA37AJaNvruYsJVanP",
            "\tIXnYw4CKd55UAwl8Zcy+M2diAbkA/0fHHcGV4r78hpbbL1Os52DPOdqYQRauIeJUeG+G6bQO",
            "MIME-Version: 1.0",
            'Content-Type: multipart/encrypted; protocol="application/pgp-encrypted";',
            '\tboundary="YFrteb74qSXmggbOxZL9dRnhymywAi"',
            "",
            "",
            "--YFrteb74qSXmggbOxZL9dRnhymywAi",
            "Content-Description: PGP/MIME version identification",
            "Content-Type: application/pgp-encrypted",
            "",
            "Version: 1",
            "",
            "",
            "--YFrteb74qSXmggbOxZL9dRnhymywAi",
            "Content-Description: OpenPGP encrypted message",
            'Content-Disposition: inline; filename="encrypted.asc";',
            'Content-Type: application/octet-stream; name="encrypted.asc"',
            "",
            "-----BEGIN PGP MESSAGE-----",
            "",
            "wU4DhW3gBZ/VvCYSAQdA8bMs2spwbKdGjVsL1ByPkNrqD7frpB73maeL6I6SzDYg",
            "O5G53tv339RdKq3WRcCtEEvxjHlUx2XNwXzC04BpmfvBTgNfPUyLDzjXnxIBB0Ae",
            "8ymwGvXMCCimHXN0Dg8Ui62KOi03h0UgheoHWovJSCDF4CKre/xtFr3nL7lq/PKI",
            "JsjVNz7/RK9FSXF6WwfONtLCyQGEuVAsB/KXfCBEyfKhaMwGHvhujRidGW5uV1no",
            "lMGl3ODmo29Lgeu2uSE7EpJRZoe6hU6ddmBkqxax61ZtkaFlGFFpdo2K8balNNdz",
            "ZsJ/9mmI9x3oOJ4/l1nhQbUO9ADbs7gJhFdV5Qkp30b5fCI7bU+aoe1ccBbLe/WM",
            "YUty1PqcuQT7XjA+XmYuL261tvW8pBetT+i33/E2d8PzzYt2IuK9qeevyS+yxdwA",
            "kfwejFWzzsUlJaDxs1x4XOxkMgSj+jo+g12dFOb7fyClsAnq23iDb8AuaT/BScAI",
            "+lO+gher69+6LmM7VGHLG5k762J1jTaQCaKt1s8TAWV99Eo4491vL6fyvk3l/Cfg",
            "RXSwiWFgj19Pn0Rq7CD9v22UE2vdUMBTcV4aw79mClk1YQ23jbF0y5DCjPdJ62Zo",
            "tskBgFt3NoWV80jZ76zIBLrrjLwCCll8JjJtFwSkt2GX5RFBsVa4A8IDht9RtEk7",
            "rrHgbSZQfkauEi/mH3/6CDZoLqSHudUZ7d4MaJwun1TkFYGe2ORwGJd4OBj3oGJp",
            "H8YBwCpk///L/fKjX0Gg3M8nrpM4wrRFhPKidAgO/kcm25X4+ZHlVkWBTCt5RWKI",
            "fHh6oLDZCqCfcgMkE1KKmwfIHaUkhq5BPRigwy6i5dh1DM4+1UCLh3dxzVbqE9b9",
            "61NB19nXdRtDA2sOUnj9ve6m/wEPyCb6/zBQZqvCBYb1/AjdXpUrFT+DbpfyxaXN",
            "XfhDVb5mNqNM/IVj0V5fvTc6vOfYbzQtPm10H+FdWWfb+rJRfyC3MA2w2IqstFe3",
            "w3bu2iE6CQvSqRvge+ZqLKt/NqYwOURiUmpuklbl3kPJ97+mfKWoiqk8Iz1VY+bb",
            "NMUC7aoGv+jcoj+WS6PYO8N6BeRVUUB3ZJSf8nzjgxm1/BcM+UD3BPrlhT11ODRs",
            "baifGbprMWwt3dhb8cQgRT8GPdpO1OsDkzL6iikMjLHWWiA99GV6ruiHsIPw6boW",
            "A6/uSOskbDHOROotKmddGTBd0iiHXAoQsJFt1ZjUkt6EHrgWs+GAvrvKpXs1mrz8",
            "uj3GwEFrHS+Xuf2UDgpszYT3hI2cL/kUtGakVR7m7vVMZqXBUbZdGAEb1PZNPwsI",
            "E4aMK02+EVB+tSN4Fzj99N2YD0inVYt+oPjr2tHhUS6aSGBNS/48Ki47DOg4Sxkn",
            "lkOWnEbCD+XTnbDd",
            "=agR5",
            "-----END PGP MESSAGE-----",
            "",
            "",
            "--YFrteb74qSXmggbOxZL9dRnhymywAi--",
            "",
            "",
        ]
    ).encode()
    for i in range(100):
        print("Sending mail", str(i))
        try:
            smtp.conn.sendmail(user, to_addr, mail)
        except smtplib.SMTPSenderRefused as e:
            assert i > 41
            assert e.smtp_code == 450
            assert b'4.7.1 Error: too much mail from' in e.smtp_error
            return
    pytest.fail("Rate limit was not exceeded")
