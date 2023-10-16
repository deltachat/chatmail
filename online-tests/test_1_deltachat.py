import random
import pytest
import time


class TestMailSending:
    def test_one_on_one(self, cmfactory, lp):
        ac1, ac2 = cmfactory.get_online_accounts(2)
        chat = cmfactory.get_accepted_chat(ac1, ac2)

        lp.sec("ac1: prepare and send text message to ac2")
        msg1 = chat.send_text("message0")

        lp.sec("wait for ac2 to receive message")
        msg2 = ac2._evtracker.wait_next_incoming_message()
        assert msg2.text == "message0"

    def test_exceed_quota(self, cmfactory, lp, tmpdir):
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
        bytes_sent = 0
        for i, msg in enumerate(msgs):
            # wait for the message to be received or to fail
            start = time.time()
            while time.time() < (start + 30):
                if msg.is_out_delivered():
                    bytes_sent += attachsize
                    mb = bytes_sent // (1024*1024)
                    lp.indent(f"message {i} success, bytes transmitted so far {mb}MB")
                    break
                elif msg.is_out_failed():
                    assert i > num_to_send/2, "quota kicked in too early"
                    lp.indent("good, message sending failed because quota was exceeded")
                    lp.indent(chat.get_messages()[i].get_message_info())
                    return
                else:
                    time.sleep(1)
        pytest.fail("sending succeeded although messages should exceed quota")
