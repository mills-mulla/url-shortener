from urllib.parse import urlsplit

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
