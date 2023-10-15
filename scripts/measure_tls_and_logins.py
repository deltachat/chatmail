
import time

import imaplib

NUM_CONNECTIONS=10

conns = []

start = time.time()
for i in range(NUM_CONNECTIONS):
    print(f"opening connection {i}")
    conn = imaplib.IMAP4_SSL("c3.testrun.org")
    conns.append(conn)

tlsdone = time.time()
duration = tlsdone-start
print(f"{duration}: TLS connections opening TLS connections")

for i, conn in enumerate(conns):
    print(f"logging into connection {i}")
    conn.login(f"measure{i}", "pass")

logindone = time.time()
duration = logindone - tlsdone
print(f"{duration}: LOGINS done")
