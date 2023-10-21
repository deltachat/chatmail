import time
import random
import pytest


class TestEndToEndDeltaChat:
    "Tests that use Delta Chat accounts on the chat mail instance."

    def test_one_on_one(self, cmfactory, lp):
        """Test that a DC account can send a message to a second DC account
        on the same chat-mail instance."""
        ac1, ac2 = cmfactory.get_online_accounts(2)
        chat = cmfactory.get_accepted_chat(ac1, ac2)

        lp.sec("ac1: prepare and send text message to ac2")
        chat.send_text("message0")

        lp.sec("wait for ac2 to receive message")
        msg2 = ac2._evtracker.wait_next_incoming_message()
        assert msg2.text == "message0"

    @pytest.mark.slow
    def test_exceed_quota(self, cmfactory, lp, tmpdir, remote):
        """This is a very slow test as it needs to upload >100MB of mail data
        before quota is exceeded, and thus depends on the speed of the upload.
        """
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
        for line in remote.iter_output("journalctl -f -u dovecot"):
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

    def test_securejoin(self, cmfactory, lp, maildomain2):
        ac1 = cmfactory.new_online_configuring_account(cache=False)
        cmfactory.switch_maildomain(maildomain2)
        ac2 = cmfactory.new_online_configuring_account(cache=False)
        cmfactory.bring_accounts_online()

        lp.sec("ac1: create QR code and let ac2 scan it, starting the securejoin")
        qr = ac1.get_setup_contact_qr()

        lp.sec("ac2: start QR-code based setup contact protocol")
        ch = ac2.qr_setup_contact(qr)
        assert ch.id >= 10
        ac1._evtracker.wait_securejoin_inviter_progress(1000)

    def test_read_receipts_between_instances(self, cmfactory, lp, maildomain2):
        ac1 = cmfactory.new_online_configuring_account(cache=False)
        cmfactory.switch_maildomain(maildomain2)
        ac2 = cmfactory.new_online_configuring_account(cache=False)
        cmfactory.bring_accounts_online()

        lp.sec("setup encrypted comms between ac1 and ac2 on different instances")
        qr = ac1.get_setup_contact_qr()
        ch = ac2.qr_setup_contact(qr)
        msg = ac2.wait_next_incoming_message()
        assert "verified" in msg.text

        lp.sec("ac1 sends a message and ac2 marks it as seen")
        chat = ac1.create_chat(ac2)
        msg = chat.send_text("hi")
        m = ac2.wait_next_incoming_message()
        m.mark_seen()
        # we can only indirectly wait for mark-seen to cause an smtp-error
        lp.sec("try to wait for markseen to complete and check error states")
        deadline = time.time() + 3.1
        while time.time() < deadline:
            msgs = m.chat.get_messages()
            for msg in msgs:
                assert "error" not in m.get_message_info()
            time.sleep(1)
