import pytest

from app.services.codes import AlPHABET,generate_code,validate_alias


def test_default_length():
    assert len(generate_code()) == 7

def test_custom_length():
    assert len(generate_code(14)) == 14

def test_only_alphabet_characters():
    code = generate_code(200)
    assert all(ch in AlPHABET for ch in code)
def test_codes_are_unique():
    codes = {generate_code() for _ in range(1000)}
    assert len(codes) == 1000

def test_valid_alias_is_returned_unchanged():
    assert validate_alias("may-link_1") == "may-link_1"

@pytest.mark.parametrize(
    "bad",
    [
        "abc",  # too short
        "a" * 33,  # too long
        "bad alias",  #has space
        "bad*alias",  # special character
        "dot.dot",  # special character
        "healthz",  # reserved
        "docs",  # reserved
        "emoji😊",  # non-ascii
    ],
)

def test_bad_aliases_rejected(bad):
    with pytest.raises(ValueError):
        validate_alias(bad)

@pytest.mark.parametrize("word",["healthz","readyz","docs","redoc","admin","api","openapi","static"])
def test_reserved_aliases_rejected(word):
    with pytest.raises(ValueError):
        validate_alias(word)