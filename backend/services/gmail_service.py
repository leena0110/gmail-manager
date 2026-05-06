"""
services/gmail_service.py — Gmail API Integration
===================================================
This service handles all communication with the Gmail API:
- Building Gmail API client with OAuth credentials
- Fetching new emails from a Gmail account
- Parsing email content (subject, body, sender, date)
- Refreshing expired access tokens automatically
"""

import os
import base64
from datetime import datetime
from email.utils import parsedate_to_datetime

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

from database import accounts_collection, emails_collection

# Load environment variables
load_dotenv()


def get_gmail_service(account):
    """
    Build a Gmail API service client for a specific account.
    
    This creates authenticated credentials from the stored tokens
    and automatically refreshes them if they've expired.
    
    Args:
        account: MongoDB document with email, access_token, refresh_token, etc.
    
    Returns:
        Gmail API service object, or None if authentication fails.
    """
    try:
        # Create credentials from stored tokens
        credentials = Credentials(
            token=account["access_token"],
            refresh_token=account["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        )

        # If the token has expired, refresh it automatically
        if credentials.expired and credentials.refresh_token:
            print(f"🔄 Refreshing token for {account['email']}...")
            credentials.refresh(Request())

            # Save the new access token back to MongoDB
            accounts_collection.update_one(
                {"email": account["email"]},
                {
                    "$set": {
                        "access_token": credentials.token,
                        "token_expiry": credentials.expiry,
                    }
                },
            )
            print(f"✅ Token refreshed for {account['email']}")

        # Build and return the Gmail API service
        service = build("gmail", "v1", credentials=credentials)
        return service

    except Exception as e:
        print(f"❌ Failed to build Gmail service for {account['email']}: {e}")
        return None


def fetch_emails_for_account(account):
    """
    Fetch new emails from a Gmail account.
    
    This function:
    1. Connects to Gmail API
    2. Gets the latest 20 messages from the inbox
    3. Checks which ones we already have in our database
    4. Downloads and parses only the NEW emails
    5. Returns a list of new email data dictionaries
    
    Args:
        account: MongoDB document with account info and tokens
    
    Returns:
        List of new email dictionaries (not yet saved to DB)
    """
    # Build the Gmail API client
    service = get_gmail_service(account)
    if not service:
        return []

    try:
        # --- Step 1: Get list of recent message IDs ---
        # We fetch the latest 20 messages from the INBOX and SPAM folders
        # (Using 'q' instead of 'labelIds' so we get an OR condition)
        results = service.users().messages().list(
            userId="me",
            q="in:inbox OR in:spam",
            maxResults=20,
        ).execute()

        messages = results.get("messages", [])

        if not messages:
            print(f"📭 No messages found for {account['email']}")
            return []

        print(f"📬 Found {len(messages)} messages for {account['email']}")

        # --- Step 2: Filter out emails we already have ---
        new_emails = []
        for msg in messages:
            gmail_id = msg["id"]

            # Check if this email already exists in our database
            existing = emails_collection.find_one({
                "gmail_id": gmail_id,
                "account_email": account["email"],
            })

            if existing:
                # We already have this email, skip it
                continue

            # --- Step 3: Fetch the full email content ---
            email_data = parse_email_message(service, gmail_id, account["email"])
            if email_data:
                new_emails.append(email_data)

        print(f"📨 {len(new_emails)} new emails for {account['email']}")
        return new_emails

    except Exception as e:
        print(f"❌ Error fetching emails for {account['email']}: {e}")
        return []


def parse_email_message(service, gmail_id, account_email):
    """
    Fetch and parse a single email message from Gmail API.
    
    Extracts the subject, sender, body text, and date from the email.
    
    Args:
        service: Gmail API service object
        gmail_id: The Gmail message ID
        account_email: The account this email belongs to
    
    Returns:
        Dictionary with parsed email data, or None if parsing fails
    """
    try:
        # Fetch the full message
        message = service.users().messages().get(
            userId="me",
            id=gmail_id,
            format="full",
        ).execute()

        # --- Extract headers (Subject, From, Date) ---
        headers = message.get("payload", {}).get("headers", [])
        subject = ""
        sender = ""
        date_str = ""

        for header in headers:
            name = header.get("name", "").lower()
            if name == "subject":
                subject = header.get("value", "(No Subject)")
            elif name == "from":
                sender = header.get("value", "Unknown")
            elif name == "date":
                date_str = header.get("value", "")

        # --- Parse the received date ---
        try:
            received_at = parsedate_to_datetime(date_str)
        except Exception:
            received_at = datetime.utcnow()

        # --- Extract the email body ---
        body = extract_body(message.get("payload", {}))

        return {
            "account_email": account_email,
            "gmail_id": gmail_id,
            "sender": sender,
            "subject": subject,
            "body": body,
            "received_at": received_at,
            # is_junk and folder will be set by the AI classifier
        }

    except Exception as e:
        print(f"❌ Error parsing email {gmail_id}: {e}")
        return None


def extract_body(payload):
    """
    Extract plain text body from a Gmail message payload.
    
    Gmail messages can be structured in different ways:
    - Simple messages have the body directly in payload.body
    - Multipart messages have the body in one of the parts
    
    This function handles both cases and decodes the base64 content.
    
    Args:
        payload: The 'payload' field from a Gmail API message
    
    Returns:
        Plain text body string (truncated to 5000 chars to save space)
    """
    body = ""

    # Case 1: Simple message — body is directly in payload
    if "body" in payload and payload["body"].get("data"):
        body = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")
        return body[:5000]  # Truncate very long emails

    # Case 2: Multipart message — look through the parts
    parts = payload.get("parts", [])
    for part in parts:
        mime_type = part.get("mimeType", "")

        # We prefer plain text over HTML
        if mime_type == "text/plain":
            data = part.get("body", {}).get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                return body[:5000]

        # If this part has sub-parts (nested multipart), recurse
        if "parts" in part:
            nested_body = extract_body(part)
            if nested_body:
                return nested_body

    # Case 3: Fall back to HTML if no plain text found
    for part in parts:
        mime_type = part.get("mimeType", "")
        if mime_type == "text/html":
            data = part.get("body", {}).get("data", "")
            if data:
                body = base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
                # Strip HTML tags for a rough plain text version
                import re
                body = re.sub(r"<[^>]+>", " ", body)
                body = re.sub(r"\s+", " ", body).strip()
                return body[:5000]

    return body if body else "(No content)"
