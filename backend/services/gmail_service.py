"""
services/gmail_service.py — Gmail API Integration
===================================================
This service handles all communication with the Gmail API:
- Building Gmail API client with OAuth credentials
- Fetching emails directly from a Gmail account (Inbox, Sent)
- Parsing email content (subject, body, sender, date)
- Sending new emails
- Refreshing expired access tokens automatically
"""

import os
import base64
from datetime import datetime
from email.utils import parsedate_to_datetime
from email.message import EmailMessage

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from dotenv import load_dotenv

from database import accounts_collection

# Load environment variables
load_dotenv()


def get_gmail_service(account):
    """
    Build a Gmail API service client for a specific account.
    """
    try:
        credentials = Credentials(
            token=account["access_token"],
            refresh_token=account["refresh_token"],
            token_uri="https://oauth2.googleapis.com/token",
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
        )

        if credentials.expired and credentials.refresh_token:
            print(f"[REFRESH] Refreshing token for {account['email']}...")
            credentials.refresh(Request())
            accounts_collection.update_one(
                {"email": account["email"]},
                {
                    "$set": {
                        "access_token": credentials.token,
                        "token_expiry": credentials.expiry,
                    }
                },
            )
            print(f"[OK] Token refreshed for {account['email']}")

        service = build("gmail", "v1", credentials=credentials)
        return service

    except Exception as e:
        print(f"[ERROR] Failed to build Gmail service for {account['email']}: {e}")
        return None


def fetch_emails_from_gmail(account, folder="inbox", max_results=20):
    """
    Fetch emails directly from Gmail for a specific folder.
    """
    service = get_gmail_service(account)
    if not service:
        return []

    try:
        query = "in:inbox"
        if folder == "sent":
            query = "in:sent"
        elif folder == "junk":
            query = "in:spam"

        results = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
        ).execute()

        messages = results.get("messages", [])
        print(f"[DEBUG] Found {len(messages)} messages for {account['email']} in {folder}")
        if not messages:
            return []

        fetched_emails = []
        for msg in messages:
            email_data = parse_email_message(service, msg["id"], account["email"])
            if email_data:
                # Format for frontend
                email_data["id"] = msg["id"]
                email_data["folder"] = folder
                email_data["is_junk"] = (folder == "junk")
                fetched_emails.append(email_data)

        print(f"[DEBUG] Successfully parsed {len(fetched_emails)} emails for {account['email']}")
        return fetched_emails

    except Exception as e:
        print(f"[ERROR] Error fetching emails for {account['email']}: {e}")
        return []


def get_single_email_from_gmail(account, gmail_id):
    """Fetch a single email directly from Gmail."""
    service = get_gmail_service(account)
    if not service:
        return None
    email_data = parse_email_message(service, gmail_id, account["email"])
    if email_data:
        email_data["id"] = gmail_id
        email_data["folder"] = "inbox"  # default fallback
        return email_data
    return None


def get_unread_count(account):
    """Get the exact number of unread emails in the inbox using Label metadata."""
    service = get_gmail_service(account)
    if not service:
        return 0
    try:
        # Fetch metadata for the INBOX label, which contains the unread count
        results = service.users().labels().get(userId="me", id="INBOX").execute()
        return results.get("messagesUnread", 0)
    except Exception as e:
        print(f"[ERROR] Could not fetch unread count for {account['email']}: {e}")
        return 0


def send_email(account, to, subject, body, attachments=None, cc=None, bcc=None):
    """Send an email using the modern EmailMessage class with real attachments, CC, and BCC."""
    service = get_gmail_service(account)
    if not service:
        return False
    
    try:
        from email.message import EmailMessage
        import re

        # Create the modern EmailMessage
        msg = EmailMessage()
        msg["To"] = to
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc
        msg["From"] = account["email"]
        msg["Subject"] = subject

        # Set the main body
        msg.set_content(re.sub(r'<[^>]+>', '', body)) # Plain text fallback
        msg.add_alternative(body, subtype='html') # HTML version

        # Handle Real Attachments
        if attachments:
            print(f"[DEBUG] Modern Send: Processing {len(attachments)} attachments...")
            for att in attachments:
                try:
                    data_str = att["data"]
                    if "," in data_str:
                        header, encoded = data_str.split(",", 1)
                        # Extract mime type
                        mime_full = header.split(":")[1].split(";")[0] if ":" in header else "application/octet-stream"
                    else:
                        encoded = data_str
                        mime_full = "application/octet-stream"
                    
                    file_data = base64.b64decode(encoded)
                    main_type, sub_type = mime_full.split("/") if "/" in mime_full else ("application", "octet-stream")
                    
                    print(f"[DEBUG] Adding part: {att['name']} ({mime_full})")
                    msg.add_attachment(
                        file_data,
                        maintype=main_type,
                        subtype=sub_type,
                        filename=att["name"]
                    )
                except Exception as e:
                    print(f"[ERROR] Failed to attach {att.get('name')}: {e}")
        else:
            print("[DEBUG] Modern Send: No attachments found.")

        # Encode and send
        raw_message = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Modern Send error: {e}")
        return False

def mark_as_read(account, gmail_id):
    """Remove the UNREAD label from a message."""
    service = get_gmail_service(account)
    if not service:
        return False
    try:
        service.users().messages().batchModify(
            userId="me",
            body={
                "ids": [gmail_id],
                "removeLabelIds": ["UNREAD"]
            }
        ).execute()
        return True
    except Exception as e:
        print(f"[ERROR] Error marking email {gmail_id} as read: {e}")
        return False



def parse_email_message(service, gmail_id, account_email):
    """Fetch and parse a single email message from Gmail API."""
    try:
        message = service.users().messages().get(
            userId="me",
            id=gmail_id,
            format="full",
        ).execute()

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

        try:
            received_at = parsedate_to_datetime(date_str)
        except Exception:
            received_at = datetime.utcnow()

        body = extract_body(message.get("payload", {}))

        return {
            "account_email": account_email,
            "gmail_id": gmail_id,
            "sender": sender,
            "subject": subject,
            "body": body,
            "received_at": received_at.isoformat() if isinstance(received_at, datetime) else received_at,
            "labelIds": message.get("labelIds", []),
        }

    except Exception as e:
        print(f"[ERROR] Error parsing email {gmail_id}: {e}")
        return None


def extract_body(payload):
    """Extract body from a Gmail message payload, preserving HTML if available."""
    # 1. Try to find HTML part (to support our rich editor)
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/html":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
            if "parts" in part:
                res = extract_body(part)
                if res and res != "(No content)": return res

    # 2. Fallback to Plain Text
    if "body" in payload and payload["body"].get("data"):
        return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="ignore")

    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/plain":
                data = part.get("body", {}).get("data", "")
                if data:
                    return base64.urlsafe_b64decode(data).decode("utf-8", errors="ignore")
    
    return "(No content)"
