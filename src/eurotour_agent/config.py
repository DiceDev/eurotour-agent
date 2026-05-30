from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env.local", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-5-mini", alias="OPENAI_MODEL")
    openai_monthly_budget_usd: float = Field(default=10.0, alias="OPENAI_MONTHLY_BUDGET_USD")

    google_client_id: str | None = Field(default=None, alias="GOOGLE_CLIENT_ID")
    google_redirect_uri: str = Field(default="http://localhost:8765/google/callback", alias="GOOGLE_REDIRECT_URI")
    google_calendar_id: str = Field(default="primary", alias="GOOGLE_CALENDAR_ID")
    spotify_client_id: str | None = Field(default=None, alias="SPOTIFY_CLIENT_ID")
    spotify_redirect_uri: str = Field(default="http://localhost:8765/callback", alias="SPOTIFY_REDIRECT_URI")
    ticketmaster_api_key: str | None = Field(default=None, alias="TICKETMASTER_API_KEY")
    amadeus_client_id: str | None = Field(default=None, alias="AMADEUS_CLIENT_ID")
    amadeus_client_secret: str | None = Field(default=None, alias="AMADEUS_CLIENT_SECRET")
    transportapi_app_id: str | None = Field(default=None, alias="TRANSPORTAPI_APP_ID")
    transportapi_app_key: str | None = Field(default=None, alias="TRANSPORTAPI_APP_KEY")


def load_settings() -> Settings:
    return Settings()
