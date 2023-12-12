import requests

dns_types = {
    "A": 1,
    "AAAA": 28,
    "CNAME": 5,
}


def resolve(domain: str) -> str:
    result = get("A", domain)
    if not result:
        result = get("CNAME", domain)
        if result:
            result = get("A", result[:-1])
            if not result:
                result = get("AAAA", domain)
    return result


def get(typ: str, domain: str) -> str:
    """Get a DNS entry"""
    url = "https://dns.nextdns.io/dns-query"
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
