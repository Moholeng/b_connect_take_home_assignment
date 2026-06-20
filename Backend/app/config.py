"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    """Runtime setting sourced from the .env file."""
    
    database_url: str 
    frontend_origin: str

    database_url = os.getenv("DATABASE_URL")
    frontend_origin = os.getenv("FRONTEND_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()