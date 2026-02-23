"""Application configuration loaded from environment variables."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Central configuration for the application."""

    # Google OAuth2
    GOOGLE_CLIENT_ID: str = os.getenv("GOOGLE_CLIENT_ID", "")
    GOOGLE_CLIENT_SECRET: str = os.getenv("GOOGLE_CLIENT_SECRET", "")
    GOOGLE_REDIRECT_URI: str = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/auth/callback")

    # AI Model
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    AI_BASE_URL: str = os.getenv("AI_BASE_URL", "https://openrouter.ai/api/v1")
    AI_MODEL: str = os.getenv("AI_MODEL", "deepseek/deepseek-r1")

    # App
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "change-me-in-production")
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    APP_PORT: int = int(os.getenv("APP_PORT", "8000"))

    # Google API Scopes
    GOOGLE_SCOPES: list[str] = [
        "https://www.googleapis.com/auth/drive",
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/presentations",
        "https://www.googleapis.com/auth/calendar",
        "https://www.googleapis.com/auth/gmail.compose",
        "https://www.googleapis.com/auth/gmail.send",
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/userinfo.profile",
        "https://www.googleapis.com/auth/userinfo.email",
    ]


settings = Settings()
