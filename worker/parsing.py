from urllib.parse import urlsplit
import ipaddress

def referrer_host(referrer:str | None ) -> str | None:
    """returns the referrer's host (lowercase, no www prefix) or None if referrer is None"""
    if referrer is None:
        return None
    host = urlsplit(referrer).hostname
    if host is None:
        return None
    if host.startswith("www."):
        host = host[4:]
    return host.lower()

def parse_device(user_agent: str | None) -> tuple[str, str]:
    """return device,browser,device is bot,tablet,mobile or other"""
    if not user_agent:
        return "other", ""
    ua = parse_ua(user_agent)
    if ua.is_bot:
        device = "bot"
    elif ua.is_tablet:
        device = "tablet"
    elif ua.is_mobile:
        device = "mobile"
    elif ua.is_desktop:
        device = "desktop"
    else:
        device = "other"
    return device,ua.Browser.family or ""


def hash_ip(ip: str, salt: str) -> str:
    data = (salt + trancate_ip(ip)).encode("utf-8")
    return hashlib.sha256(data).hexdigest()[:16]

def truncate_ip(client_ip: str) -> str:
    """ IPV4 -> its /24 networks v6 is /48. rise ValueError if invalid"""
    addr = ipaddress.ip_address(client-ip.strip())
    if addr.version == 6 and addr.ipv4_mapped: # ::fff
        addr = addr.ipv4_mapped
    if addr.version == 4:
        return str(ip_address.ip_network(f"{addr}/24", strict=False).network_address)
    return ":" .join(addr.exploded.split(":")[:3]) + "::"


    

   