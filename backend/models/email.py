"""
models/email.py — Email Data Schema
====================================
Defines the data structure for an email stored in MongoDB.
Each email belongs to a specific Gmail account and is classified
as either "inbox" or "junk" by our AI classifier.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EmailBase(BaseModel):
    """
    Base schema for an email document in MongoDB.
    """
    account_email: str          # Which Gmail account this email belongs to
    gmail_id: str               # Unique ID from Gmail API (prevents duplicates)
    sender: str                 # Who sent the email (From field)
    subject: str                # Email subject line
    body: str                   # Email body content (plain text)
    received_at: datetime       # When the email was received
    is_junk: bool               # True if AI classified it as junk/spam
    folder: str                 # "inbox" or "junk"


class EmailResponse(BaseModel):
    """
    Schema for returning email data to the frontend.
    """
    id: str                     # MongoDB document ID (as string)
    account_email: str          # Which account this belongs to
    gmail_id: str               # Gmail's unique message ID
    sender: str                 # From address
    subject: str                # Subject line
    body: str                   # Email body
    received_at: datetime       # When received
    is_junk: bool               # Junk classification result
    folder: str                 # "inbox" or "junk"
