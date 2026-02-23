"""Google OAuth2 authentication service.

Handles the full OAuth2 flow: generating auth URLs, exchanging codes for
tokens, refreshing tokens, and building authenticated Google API service
objects.
"""

import json
import os
from typing import Optional

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request

from app.config import settings

# Google bazen otomatik olarak `openid` gibi ekstra yetkiler döndürür.
# İstediğimiz yetkilerle Google'ın döndüğü %100 uyuşmadığında güvenlik hatası fırlatmaması için
# bu esnekliği aktif ediyoruz.
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

TOKEN_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "token.json")


def _client_config() -> dict:
    """Return the OAuth client config dict expected by google-auth."""
    return {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }


def get_auth_url() -> str:
    """Generate the Google OAuth2 authorization URL."""
    flow = Flow.from_client_config(
        _client_config(),
        scopes=settings.GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    return auth_url


def exchange_code(code: str) -> Credentials:
    """Exchange an authorization code for credentials and persist them."""
    flow = Flow.from_client_config(
        _client_config(),
        scopes=settings.GOOGLE_SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI,
    )
    flow.fetch_token(code=code)
    creds = flow.credentials
    _save_credentials(creds)
    return creds


def get_credentials() -> Optional[Credentials]:
    """Load stored credentials, refreshing if expired."""
    if not os.path.exists(TOKEN_PATH):
        return None

    creds = Credentials.from_authorized_user_file(TOKEN_PATH, settings.GOOGLE_SCOPES)

    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        _save_credentials(creds)

    if creds and creds.valid:
        return creds

    return None


def is_authenticated() -> bool:
    """Check whether valid credentials exist."""
    return get_credentials() is not None


def logout():
    """Remove stored credentials."""
    if os.path.exists(TOKEN_PATH):
        os.remove(TOKEN_PATH)


def _save_credentials(creds: Credentials):
    """Persist credentials to disk."""
    with open(TOKEN_PATH, "w") as f:
        f.write(creds.to_json())
