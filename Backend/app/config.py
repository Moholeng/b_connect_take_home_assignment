"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings sourced from the environment or a .env file."""

    database_url: str
    frontend_origin: str = "http://localhost:5173"
    openai_api_key: str | None = None 

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()