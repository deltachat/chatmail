def test_remotelog(remotelog, imap_or_smtp):
    lineproducer = remotelog.iter(imap_or_smtp.logunit)
    imap_or_smtp.connect()
    assert imap_or_smtp.logunit in next(lineproducer)
