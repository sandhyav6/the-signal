"""
config.py — Application configuration.

Loads settings from environment variables (or a .env file if present).
All settings have safe defaults so the app runs in mock mode with no
.env file configured.
"""

import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application-wide settings loaded from environment variables.

    Attributes:
        news_api_key: NewsAPI.org API key. Empty string = mock mode.
        news_api_url: Base URL for NewsAPI.
        database_url: SQLAlchemy connection string. Defaults to local SQLite.
        app_env: "mock" or "live". Controls whether live API calls are made.
        backend_host: FastAPI host.
        backend_port: FastAPI port.
        frontend_port: Streamlit port.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # News API
    news_api_key: str = ""
    news_api_url: str = "https://newsapi.org/v2"

    # Database
    database_url: str = "sqlite:///./data/news.db"

    # Application mode
    app_env: str = "mock"  # "mock" | "live"

    # Server
    backend_host: str = "127.0.0.1"
    backend_port: int = 8000
    frontend_port: int = 8501

    @property
    def is_live_mode(self) -> bool:
        """Return True only when both APP_ENV=live and a key is present."""
        return self.app_env == "live" and bool(self.news_api_key)

    @property
    def mock_data_path(self) -> str:
        """Absolute path to the mock articles JSON file."""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "data", "mock_articles.json")


# Module-level singleton — import this everywhere.
settings = Settings()
