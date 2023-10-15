import os.path
import random
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

        ac2.set_config("download_limit", 1024 * 2)  # set download_limit to 2 KB avoid downloading all those 5MB files

        lp.sec("ac1: send 25 5 MB files to ac2")
        alphanumeric = "abcdefghijklmnopqrstuvwxyz1234567890"
        for i in range(25):
            attachment = tmpdir / f"attachment{i}"
            with open(attachment, "w+") as f:
                for j in range(1024 * 1024 * 5):
                    f.write(random.choice(alphanumeric))

            print("Sent out msg", str(i))
            chat.send_file(str(attachment))

        ac2.wait_next_incoming_message()
        lp.sec("ac2: check that at least one message failed")
        failed = False
        for i in range(25):
            if chat.get_messages()[i].is_out_failed():
                failed = True
                print(chat.get_messages()[i].get_message_info())
        try:
            assert failed
        except:
            import pdb; pdb.set_trace()
