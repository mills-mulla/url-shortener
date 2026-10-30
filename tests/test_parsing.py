
import pytest
from worker.parsing import referrer_host

@pytest.mark.parametrize(
    "referrer, expected",
    [
        ("https://www.t.co/x", "t.co"),
        ("https://Google.com/search?q=1", "google.com"),
        ( None, None)
    ],

)
def test_referrer_host(referrer, expected):
    assert referrer_host(referrer) == expected