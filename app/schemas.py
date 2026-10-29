from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator
from app.services.codes import validate_alias
from app.services.urls import MAX_URL_LENGTH

def _check_expiry(value:datetime | None) -> datetime | None:
    """Expiry must carry a timezone ans bein the future."""
    if value is None:
        return None
    if value.tzinfo is None:
        raise ValueError("Expiry must carry a timezone.")
    if value < datetime.now(timezone.utc):
        raise ValueError("Expiry must be in the future.")

    return value

#==================Users====================

class UserCreate(BaseModel):
    email: EmailStr

class UserCreated(BaseModel):
    id: int
    email: EmailStr
    api_key: str

#==================Links====================

class LinkCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    url: str = Field(min_length = 1, max_length=MAX_URL_LENGTH)
    alias:str |None = None
    expires_at: datetime | None = None

    @field_validator("alias")
    @classmethod
    def check_alias(cls, value:str | None) -> str | None:
      return None if value is None else validate_alias(value)

    @field_validator("expires_at")
    @classmethod
    def check_expiry(cls, value:datetime | None) -> datetime | None:
        return _check_expiry(value) 
    
class LinkUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    url: str | None = Field(default=None, min_length = 1, max_length=MAX_URL_LENGTH)
    is_active: bool | None = None
    expires_at: datetime | None = None

    @field_validator("expires_at")
    @classmethod
    def check_expiry(cls, value:datetime | None) -> datetime | None:
        return _check_expiry(value)
    
class LinkOut(BaseModel):
    code: str
    short_url: str
    target_url: str
    is_active: bool
    expires_at: datetime | None 
    created_at: datetime

#==================Sats===============

class DayCount(BaseModel):
    day:str
    clicks: int

class ReferrerCount(BaseModel):
    referrer:str
    clicks:int

class DeviceCount(BaseModel):
        device:str
        clicks:int
    
class countryCount(BaseModel):
    country:str
    clicks:int

class StatsOut(BaseModel):
    total_clicks:int
    by_day: list[DayCount]
    top_referrers: list[ReferrerCount]
    devices: list[DeviceCount]
    countries: list[countryCount]