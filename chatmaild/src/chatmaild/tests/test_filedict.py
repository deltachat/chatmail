from chatmaild.filedict import FileDict


def test_basic(tmp_path):
    fdict = FileDict(tmp_path.joinpath("metadata"))
    assert fdict.read() == {}
    with fdict.modify() as d:
        d["devicetoken"] = [1, 2, 3]
        d["456"] = 4.2
    new = fdict.read()
    assert new["devicetoken"] == [1, 2, 3]
    assert new["456"] == 4.2


def test_dying_lock(tmp_path, caplog):
    fdict1 = FileDict(tmp_path.joinpath("metadata"))
    fdict2 = FileDict(tmp_path.joinpath("metadata"), timeout=0.1)
    with fdict1.modify() as d:
        with fdict2.modify() as d2:
            d2["1"] = "2"
        assert "could not obtain" in caplog.records[0].msg
        d["1"] = "3"
    assert fdict1.read()["1"] == "3"
    assert fdict2.read()["1"] == "3"


def test_bad_marshal_file(tmp_path, caplog):
    fdict1 = FileDict(tmp_path.joinpath("metadata"))
    fdict1.path.write_bytes(b"l12k3l12k3l")
    assert fdict1.read() == {}
    assert "corrupt" in caplog.records[0].msg
