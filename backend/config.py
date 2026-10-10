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
        news_api_country: 2-letter country code for top headlines.
        news_api_page_size: articles requested per category (max 100).
        news_api_daily_budget: max NewsAPI requests per UTC day (the free
            developer plan allows 100; a margin is kept for manual use).
        refresh_cooldown_seconds: minimum gap between live fetches — a
            refresh inside this window is served from the cached database.
        auto_refresh_minutes: background live-refresh interval (0 = off).
        serve_frontend: serve the built React app (frontend/dist) from this
            backend, with the API only under /api — used in deployment.
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
    news_api_country: str = "us"
    news_api_page_size: int = 40
    news_api_daily_budget: int = 90
    refresh_cooldown_seconds: int = 300
    auto_refresh_minutes: int = 180

    # Deployment
    serve_frontend: bool = False

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
    def has_news_api_key(self) -> bool:
        """Return True if a NewsAPI key is configured (live mode possible)."""
        return bool(self.news_api_key.strip())

    @property
    def mock_data_path(self) -> str:
        """Absolute path to the mock articles JSON file."""
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.join(base, "data", "mock_articles.json")


# Module-level singleton — import this everywhere.
settings = Settings()
