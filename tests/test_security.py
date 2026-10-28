from app.services.security import hash_key, new_api_key

def test_key_has_prefix():
    key, _ = new_api_key()
    assert key.startswith("sk_") 

def test_hash_maches_key():
    key, key_hash = new_api_key()
    assert key_hash == hash_key(key)

def test_hash_length():
    _, key_hash = new_api_key()
    assert len(key_hash) == 64

def test_keys_are_unique():
    key1,_ = new_api_key()
    key2,_ = new_api_key()
    assert key1 != key2

def test_known_hash():
    assert hash_key("abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
