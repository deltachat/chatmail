def test_remotelog(remotelog, imap_or_smtp):
    lineproducer = remotelog.iter(imap_or_smtp.logunit)
    imap_or_smtp.connect()
    assert imap_or_smtp.logunit in next(lineproducer)


def test_use_two_chatmailservers(cmfactory, maildomain2, switch_maildomain):
    (ac1,) = cmfactory.get_online_accounts(1)
    with switch_maildomain(cmfactory, maildomain2):
        (ac2,) = cmfactory.get_online_accounts(1)
    cmfactory.get_accepted_chat(ac1, ac2)
    domain1 = ac1.get_config("addr").split("@")[1]
    domain2 = ac2.get_config("addr").split("@")[1]
    assert domain1 != domain2
