from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="app_env", extra="ignore")

    app_env: str = "dev"
    base_url: str = "http://localhost:8000"
    database_url: str
    redis_url: str
    code_length: int = 7
    cache_ttl_seconds: int = 3600
    rate_limit_crate_per_min: int = 30
    stream_name: str = "clicks:stream"
    stream_maxlen: int = 100000
    geoip_db_path: str = "/data/GEoLitez-Country.mmdb"

settings = Settings()