import pytest

from cmdeploy import remote_funcs
from cmdeploy.dns import check_initial_remote_data


@pytest.fixture
def mockdns_base(monkeypatch):
    qdict = {}

    def query_dns(typ, domain):
        try:
            return qdict[typ][domain]
        except KeyError:
            return ""

    monkeypatch.setattr(remote_funcs, query_dns.__name__, query_dns)
    return qdict


@pytest.fixture
def mockdns(mockdns_base):
    mockdns_base.update(
        {
            "A": {"some.domain": "1.1.1.1"},
            "AAAA": {"some.domain": "fde5:cd7a:9e1c:3240:5a99:936f:cdac:53ae"},
            "CNAME": {"mta-sts.some.domain": "some.domain"},
        }
    )
    return mockdns_base


class TestPerformInitialChecks:
    def test_perform_initial_checks_ok1(self, mockdns):
        remote_data = remote_funcs.perform_initial_checks("some.domain")
        assert len(remote_data) == 7

    @pytest.mark.parametrize("drop", ["A", "AAAA"])
    def test_perform_initial_checks_with_one_of_A_AAAA(self, mockdns, drop):
        del mockdns[drop]
        remote_data = remote_funcs.perform_initial_checks("some.domain")
        assert len(remote_data) == 7
        assert not remote_data[drop]

        l = []
        res = check_initial_remote_data(remote_data, print=l.append)
        assert res
        assert not l

    def test_perform_initial_checks_no_mta_sts(self, mockdns):
        del mockdns["CNAME"]
        remote_data = remote_funcs.perform_initial_checks("some.domain")
        assert len(remote_data) == 4
        assert not remote_data["MTA_STS"]

        l = []
        res = check_initial_remote_data(remote_data, print=l.append)
        assert not res
        assert len(l) == 2


def parse_zonefile_into_dict(zonefile, mockdns_base):
    for zf_line in zonefile.split("\n"):
        if not zf_line.strip() or zf_line.startswith("#"):
            continue
        zf_domain, zf_typ, zf_value = zf_line.split(maxsplit=2)
        zf_domain = zf_domain.rstrip(".")
        zf_value = zf_value.strip()
        mockdns_base.setdefault(zf_typ, {})[zf_domain] = zf_value


def test_check_zonefile_all_ok(data, mockdns_base):
    zonefile = data.get("zftest.zone")
    parse_zonefile_into_dict(zonefile, mockdns_base)
    required_diff, recommended_diff = remote_funcs.check_zonefile(zonefile)
    assert not required_diff and not recommended_diff


def test_check_zonefile_recommended_not_set(data, mockdns_base):
    zonefile = data.get("zftest.zone")

    zonefile_mocked = zonefile.split("# Recommended")[0]
    parse_zonefile_into_dict(zonefile_mocked, mockdns_base)
    required_diff, recommended_diff = remote_funcs.check_zonefile(zonefile)
    assert not required_diff
    assert len(recommended_diff) == 8
