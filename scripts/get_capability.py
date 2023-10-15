import os
import time
import imaplib

domain = os.environ.get("CHATMAIL_DOMAIN", "c3.testrun.org")

print("connecting")
conn = imaplib.IMAP4_SSL(domain)
print("logging in")
conn.login(f"measure{time.time()}", "pass")
print(conn.capability())
