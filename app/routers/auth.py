"""Authentication routes – handles Google OAuth2 login/callback/logout."""

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

from app.services.google_auth import get_auth_url, exchange_code, is_authenticated, logout

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.get("/status")
async def auth_status():
    """Check if user is authenticated."""
    return {"authenticated": is_authenticated()}


@router.get("/login")
async def login():
    """Redirect user to Google OAuth2 consent page."""
    url = get_auth_url()
    return RedirectResponse(url=url)


@router.get("/callback")
async def callback(code: str):
    """Handle the OAuth2 callback and store credentials."""
    try:
        exchange_code(code)
        return RedirectResponse(url="/")
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"error": f"Authentication failed: {str(e)}"},
        )


@router.post("/logout")
async def logout_route():
    """Remove stored credentials."""
    logout()
    return {"status": "logged_out"}
