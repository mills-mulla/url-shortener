import pytest

from app.services.urls import MAX_URL_LENGTH, ALLOWED_SCHEMES, validate_target

OWN = "short.test"

@pytest.mark.parametrize(
    "good",
    [
        "https://example.com",
        "http://example.com/path?q1#frag",
        "HTTPS://EXAMPLE.COM/A",
    ],
)
def test_valid_urls_accepted(good):
    assert validate_target(good, OWN) == good

def test_surrounding_whitespace_striped():
    assert validate_target("  https://example.com  ", OWN) == "https://example.com"

def test_max_length_boundary_accepted():
    url = "http://example.com/" + "a" * (MAX_URL_LENGTH - len("http://example.com/"))
    assert len(url) == MAX_URL_LENGTH
    assert validate_target(url, OWN) == url

def test_tool_long_rejected():
    url = "http://example.com/" + "a" * MAX_URL_LENGTH 
    with pytest.raises(ValueError):
        validate_target(url, OWN)

@pytest.mark.parametrize(
    "bad",
    [
        "",
        "data:text/html,hi",
        "file://etc/passws",
        "http://example.com:99999",
        "https:///path",
        "https://google.com@example.com"
    ]
)
def test_bad_urls_rejected(bad):
    with pytest.raises(ValueError):
        validate_target(bad, OWN)

@pytest.mark.parametrize(
    "own",
    [
        "https://short.test",
        "https://SHORT.TEST",
        "https://short.test:8080",
    ]
)
def test_own_host_rejected(own):
    with pytest.raises(ValueError):
        validate_target(own, OWN)

def test_lookalike_host_allowed():
    url = "https://short.test.evil.com"