def test_tls_serialized_connect(benchmark, imap_or_smtp):
    def connect():
        imap_or_smtp.connect()

    benchmark(connect)


def test_login(benchmark, imap_or_smtp, gencreds):
    cls = imap_or_smtp.__class__
    conns = []
    for i in range(20):
        conn = cls(imap_or_smtp.host)
        conn.connect()
        conns.append(conn)

    def login():
        conn = conns.pop()
        conn.login(*gencreds())

    benchmark(login)


def test_send_and_receive_10(benchmark, cmfactory, lp):
    """send many messages between two accounts"""
    ac1, ac2 = cmfactory.get_online_accounts(2)
    chat = cmfactory.get_accepted_chat(ac1, ac2)

    def send_10_receive_all():
        for i in range(10):
            chat.send_text(f"hello {i}")
        for i in range(10):
            ac2.wait_next_incoming_message()

    benchmark(send_10_receive_all)
