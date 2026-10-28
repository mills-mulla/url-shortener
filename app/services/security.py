import hashlib
import secrets

KEY_PREFIX = "sk_"

def hash_key(key:str) ->str:
    """ Return the SHA-256 hec digest of the key."""
    return hashlib.sha256(key.encode("utf-8")).hexdigest()

def new_api_key() ->tuple[str,str]:
    """ Return (plaintext_key,key_hash).The key looks like "sk_<random>."""
    key = KEY_PREFIX + secrets.token_urlsafe(32)
    return key, hash_key(key)