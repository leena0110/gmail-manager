"""
models/account.py — Account Data Schema
========================================
Defines the data structure for a Gmail account stored in MongoDB.
Used for validation when adding or returning account data.
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class AccountBase(BaseModel):
    """
    Base schema for a Gmail account.
    This represents the data we store in the 'accounts' collection.
    """
    email: str                          # The Gmail address (e.g., user@gmail.com)
    access_token: str                   # OAuth2 access token for Gmail API
    refresh_token: str                  # OAuth2 refresh token (used to get new access tokens)
    token_expiry: Optional[datetime]    # When the access token expires
    added_at: datetime                  # When this account was added to our app


class AccountResponse(BaseModel):
    """
    Schema for returning account data to the frontend.
    We DON'T send tokens to the frontend — that would be a security risk!
    """
    id: str                             # MongoDB document ID (as string)
    email: str                          # The Gmail address
    added_at: datetime                  # When the account was added
