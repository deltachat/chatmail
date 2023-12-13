import requests

url = "https://dns.nextdns.io/dns-query"
dns_types = {
    "A": 1,
    "AAAA": 28,
    "CNAME": 5,
    "MX": 15,
    "SRV": 33,
    "CAA": 257,
    "TXT": 16,
}


def get(typ: str, domain: str) -> str:
    """Get a DNS entry"""
    r = requests.get(
        url,
        params={"name": domain, "type": typ},
        headers={"accept": "application/dns-json"},
    )

    j = r.json()
    if "Answer" in j:
        for answer in j["Answer"]:
            if answer["type"] == dns_types[typ]:
                return answer["data"]
    return ""


def resolve_mx(domain: str) -> (str, str):
    """Resolve an MX entry"""
    r = requests.get(
        url,
        params={"name": domain, "type": "MX"},
        headers={"accept": "application/dns-json"},
    )

    j = r.json()
    if "Answer" in j:
        result = (0, None)
        for answer in j["Answer"]:
            if answer["type"] == dns_types["MX"]:
                prio, server_name = answer["data"].split()
                if int(prio) > result[0]:
                    result = (int(prio), server_name)
        return result
    return None, None


def resolve(domain: str) -> str:
    result = get("A", domain)
    if not result:
        result = get("CNAME", domain)
        if result:
            result = get("A", result[:-1])
            if not result:
                result = get("AAAA", domain)
    return result
