from datetime import datetime, timezone
import pytest
from app.services.events import MAX_REFERRER, MAX_UA, build_click_event

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)

def test_all_values_are_strings():
    ev = build_click_event(5, "https/t.co/x", "UA", "203.0.113.77", NOW)
    assert all(isinstance(v, str) for  v in ev.values())

def test_ip_is_truncated():
    assert build_click_event(1, None, None, "203.0.113.77", NOW)["ip24"] == "203.0.113.0"

def test_bad_or_missing_ip_gives_empty_string():
   assert build_click_event(1, None, None, "badip", NOW)["ip24"] == ""
   assert build_click_event(1, None, None, None, NOW)["ip24"] == ""

def test_native_time_rejected():
    with pytest.raises(ValueError):
        build_click_event(1, None, None, None, datetime(2023, 1, 1))
    
def test_ts_is_utc_iso():
    assert build_click_event(1, None, None, None, NOW)["ts"].endswith("+00:00")