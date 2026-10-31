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

def parse_device():
    pass
    
def hash_ip():
    pass

def truncate_ip(client_ip: str) -> str:
    pass
#     try:
#         addr = ipaddress.ip_address(client_ip)
#         if isinstance(addr, ipaddress.IPv4Address):
#             # Zero out the last octet: 192.168.1.50 -> 192.168.1.0
#             parts = client_ip.split(".")
#             return f"{parts[0]}.{parts[1]}.{parts[2]}.0"
#         elif isinstance(addr, ipaddress.IPv6Address):
#             # Keep the first 3 blocks (/48 prefix)
#             compressed = addr.exploded
#             return ":".join(compressed.split(":")[:3]) + "::"
#     except ValueError:
#         pass
#     return "0.0.0.0"
   