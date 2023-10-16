import random
import pytest


class TestMailSending:
    def test_one_on_one(self, cmfactory, lp):
        ac1, ac2 = cmfactory.get_online_accounts(2)
        chat = cmfactory.get_accepted_chat(ac1, ac2)

        lp.sec("ac1: prepare and send text message to ac2")
        chat.send_text("message0")

        lp.sec("wait for ac2 to receive message")
        msg2 = ac2._evtracker.wait_next_incoming_message()
        assert msg2.text == "message0"

    def test_exceed_quota(self, cmfactory, lp, tmpdir, dovelogreader):
        ac1, ac2 = cmfactory.get_online_accounts(2)
        chat = cmfactory.get_accepted_chat(ac1, ac2)

        quota = 1024 * 1024 * 100
        attachsize = 1 * 1024 * 1024
        num_to_send = quota // attachsize + 2
        lp.sec(f"ac1: send {num_to_send} large files to ac2")
        lp.indent(f"per-user quota is assumed to be: {quota/(1024*1024)}MB")
        alphanumeric = "abcdefghijklmnopqrstuvwxyz1234567890"
        msgs = []
        for i in range(num_to_send):
            attachment = tmpdir / f"attachment{i}"
            data = "".join(random.choice(alphanumeric) for i in range(1024))
            with open(attachment, "w+") as f:
                for j in range(attachsize // len(data)):
                    f.write(data)

            msg = chat.send_file(str(attachment))
            msgs.append(msg)
            lp.indent(f"Sent out msg {i}, size {attachsize/(1024*1024)}MB")

        lp.sec("ac2: check messages are arriving until quota is reached")

        addr = ac2.get_config("addr").lower()
        saved_ok = 0
        for line in dovelogreader():
            line = line.decode().lower().strip()
            if addr not in line:
                # print(line)
                continue
            if "quota" in line:
                if "quota exceeded" in line:
                    if saved_ok < num_to_send // 2:
                        pytest.fail(
                            f"quota exceeded too early: after {saved_ok} messages already"
                        )
                    lp.indent("good, message sending failed because quota was exceeded")
                    return
            if "saved mail to inbox" in line:
                saved_ok += 1
                print(f"{saved_ok}: {line}")
                if saved_ok >= num_to_send:
                    break

        pytest.fail("sending succeeded although messages should exceed quota")
