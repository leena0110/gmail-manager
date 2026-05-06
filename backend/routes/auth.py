"""
routes/auth.py — Google OAuth2 Authentication Routes
=====================================================
Handles the Google OAuth2 login flow:
1. /auth/login   → Generates a Google login URL for the user
2. /auth/callback → Google redirects here after login; we exchange
                     the auth code for tokens and save the account
"""

import os
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from google_auth_oauthlib.flow import Flow
from dotenv import load_dotenv

from database import accounts_collection

# Load environment variables
load_dotenv()

# Relax the OAuth scope check — allows Google to return fewer scopes
# than we requested without raising an error
os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"

# Create the router for auth-related endpoints
router = APIRouter()

# --- Google OAuth2 Configuration ---
# These scopes define what permissions we're asking for
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",  # Read emails
    "https://www.googleapis.com/auth/userinfo.email",   # Get user's email address
    "openid",                                            # OpenID Connect
]

# Build the OAuth client config from environment variables
CLIENT_CONFIG = {
    "web": {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "redirect_uris": [os.getenv("GOOGLE_REDIRECT_URI")],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

# Store the code_verifier between /login and /callback requests.
# Needed because Google's OAuth library uses PKCE by default —
# the verifier is generated during login but must be re-used in callback.
_pending_code_verifier = None


def create_oauth_flow():
    """
    Creates a new Google OAuth2 flow instance.
    This is used for both generating the login URL and handling the callback.
    """
    flow = Flow.from_client_config(
        CLIENT_CONFIG,
        scopes=SCOPES,
        redirect_uri=os.getenv("GOOGLE_REDIRECT_URI"),
    )
    return flow


# ============================================
# ENDPOINT: GET /auth/login
# ============================================
# Purpose: Generate a Google OAuth2 login URL
# The frontend calls this, then redirects the user to Google's login page
@router.get("/login")
async def login():
    """
    Step 1 of OAuth: Generate the Google login URL.
    The user will be redirected to Google to sign in and approve access.
    """
    global _pending_code_verifier

    flow = create_oauth_flow()

    # Generate the authorization URL
    # access_type="offline" gives us a refresh_token so we can fetch emails later
    # prompt="consent" forces Google to show the consent screen every time
    #   (this ensures we always get a refresh_token)
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        prompt="consent",
        include_granted_scopes="true",
    )

    # Save the PKCE code_verifier so we can use it in the callback
    _pending_code_verifier = flow.code_verifier

    return {"auth_url": authorization_url}


# ============================================
# ENDPOINT: GET /auth/callback
# ============================================
# Purpose: Handle the redirect from Google after the user logs in
# Google sends us an authorization code, which we exchange for tokens
@router.get("/callback")
async def callback(code: str):
    """
    Step 2 of OAuth: Google redirects here with an authorization code.
    We exchange that code for access_token and refresh_token,
    then save the account to MongoDB.
    """
    global _pending_code_verifier

    try:
        flow = create_oauth_flow()

        # Restore the PKCE code_verifier from the login step
        flow.code_verifier = _pending_code_verifier

        # Exchange the authorization code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials

        # Get the user's email address from the ID token
        # The ID token contains user info like email
        from google.oauth2 import id_token
        from google.auth.transport import requests

        id_info = id_token.verify_oauth2_token(
            credentials.id_token,
            requests.Request(),
            os.getenv("GOOGLE_CLIENT_ID"),
            clock_skew_in_seconds=120,  # Allow 2 min clock difference
        )

        user_email = id_info.get("email")

        if not user_email:
            raise HTTPException(status_code=400, detail="Could not get email from Google")

        # --- Save or update the account in MongoDB ---
        account_data = {
            "email": user_email,
            "access_token": credentials.token,
            "refresh_token": credentials.refresh_token,
            "token_expiry": credentials.expiry,
            "added_at": datetime.utcnow(),
        }

        # Use upsert: if account exists, update tokens; if not, create it
        accounts_collection.update_one(
            {"email": user_email},           # Find by email
            {"$set": account_data},          # Update these fields
            upsert=True,                     # Create if doesn't exist
        )

        print(f"✅ Account added/updated: {user_email}")

        # Redirect the user back to the frontend dashboard
        return RedirectResponse(url="http://localhost:5173/oauth/callback?success=true")

    except Exception as e:
        print(f"❌ OAuth callback error: {e}")
        return RedirectResponse(
            url=f"http://localhost:5173/oauth/callback?error={str(e)}"
        )
