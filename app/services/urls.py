from urllib.parse import urlsplit

MAX_URL_LENGTH = 2048
ALLOWED_SCHEMES = ["http", "https"]

def validate_target(url:str ,own_host:str) ->str:
    """Return the cleaned url if it is safe to shoten, ortherwise raise ValueError
    own_host is our own hostname like "example.com" without a port
    
    """

    url = url.strip()
    if not url:
        raise ValueError("URL is required")
    if len(url) > MAX_URL_LENGTH:
        raise ValueError(f"URL is longer than  {MAX_URL_LENGTH} characters")
    if any(ch.isspace() or ord(ch) < 32 or ord(ch)==127 for ch in url):
        raise ValueError("URL must not contain spaces or control characters")

    parts = urlsplit(url)
    if parts.scheme not in ALLOWED_SCHEMES:
        raise ValueError(f"URL scheme must be one of {ALLOWED_SCHEMES}")
    if not parts.hostname:
        raise ValueError("URL must include a host")
    if parts.username or parts.password:
        raise ValueError("URLs with embeded credentials are not allowed")
    

    try:
        _=parts.port
    except ValueError:
        raise ValueError("URL has invalid port") from None

    if parts.hostname == own_host.lower():
        raise ValueError("cannot shorten a link to this service")

    return url


