import re
import secrets

AlPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"

RESERVED = {
    "healthz",
    "readyz",
    "docs",
    "redoc",
    "admin",
    "api",
    "openapi",
    "static"
}

ALIAS_PATTERN = re.compile(r"[A-Za-z0-9_-]{4,32}")

def generate_code(length:int = 7) ->str:
    """ Return a random short code eg "abc1234"."""
    return "".join(secrets.choice(AlPHABET) for _ in range(length))

def validate_alias(alias:str) ->str:
    """Return the alias if it is allowed,ortherwisw raise ValueError"""
    if not ALIAS_PATTERN.fullmatch(alias):
        raise ValueError("Alias must be 4-32 characters:letters, numbers, hyphens, or underscores.")
    if alias.lower() in RESERVED:
        raise ValueError("That alias is reserved")
    return alias
