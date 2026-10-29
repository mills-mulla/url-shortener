from datetime import datetime,timedelta,timezone
import pytest
from pydantic import ValidationError
from app.schemas import UserCreate, LinkCreate, LinkUpdate

FUTURE = datetime.now(timezone.utc) + timedelta(days=1)
PAST = datetime.now(timezone.utc) - timedelta(days=1)

def  test_link_create_minimal():
    link = LinkCreate(url="https://example.com")
    assert link.alias is None
    assert link.expires_at is None

def test_link_create_with_strips_whitespace():
    assert LinkCreate(url="  https://example.com   ").url== "https://example.com"

def test_empty_url_rejected():
    with pytest.raises(ValidationError):
        LinkCreate(url="")  

def test_past_expiry_rejected():
    with pytest.raises(ValidationError):
        LinkCreate(url="https://example.com", expires_at=PAST)

def test_bad_email_rejected():
    with pytest.raises(ValidationError):
        UserCreate(email="not-an-email")
