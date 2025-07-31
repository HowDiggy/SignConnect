# src/signconnect/core/config.py
from functools import lru_cache
from typing import Any

from pydantic import PostgresDsn, computed_field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Represents the application settings.

    Reads configuration from environment variables and/or a .env file.
    The DATABASE_URL is now a computed field, assembled from its component parts,
    which is more secure and flexible for different environments (dev, test, prod).
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- LLM and Firebase API Keys ---
    GEMINI_API_KEY: SecretStr
    FIREBASE_CLIENT_API_KEY: SecretStr

    # --- Database Component Settings ---
    POSTGRES_SERVER: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: SecretStr
    POSTGRES_DB: str

    @computed_field
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        """
        Assembles the database connection string from its components.

        This computed field ensures that the application has a valid
        PostgreSQL DSN to connect to the database.
        """
        return PostgresDsn.build(
            scheme="postgresql",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD.get_secret_value(),
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=f"{self.POSTGRES_DB}",
        )


@lru_cache
def get_settings() -> Settings:
    """
    Returns the cached settings instance for the application.
    """
    return Settings()