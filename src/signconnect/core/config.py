# config.py
# For loading environment variables (e.g., API keys)

from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache

class Settings(BaseSettings):
    """
    Represents the application settings.
    Reads configuration settings from environment variables and/or a .env file.
    """

    # this tells pydantic to load variables from a .env file.
    # the path is relative to where you run your application.
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False, # allows for DATABASE_URL or database_url
    )

    # define your settings here. Pydantic will automatically read
    # the corresponding environment variable
    DATABASE_URL: str

# the @lru_cache decorator caches the Settings object. This means the .env file is
# only read once, the first time this function is called
@lru_cache
def get_settings() -> Settings:
    """
    Returns the cached settings instance for the application.
    :return:
    """
    return Settings()