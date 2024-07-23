from chatmaild.metrics import main


def test_main(tmp_path, capsys):
    for x in ("ci-asllkj", "ac_12l3kj", "qweqwe", "ci-l1k2j31l2k3"):
        tmp_path.joinpath(x).mkdir()
    main(tmp_path)
    out, _ = capsys.readouterr()
    d = {}
    for line in out.split("\n"):
        if line.strip() and not line.startswith("#"):
            name, num = line.split()
            d[name] = int(num)

    assert d["accounts"] == 4
    assert d["ci_accounts"] == 3
    assert d["nonci_accounts"] == 1
