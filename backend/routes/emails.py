"""
routes/emails.py — Email Retrieval Routes
==========================================
Handles fetching emails from the database:
1. GET /emails/{email}         → Get all emails for an account
2. GET /emails/{email}/inbox   → Get only inbox emails
3. GET /emails/{email}/junk    → Get only junk emails
4. GET /emails/{email}/{gmail_id} → Get a single email by Gmail ID
"""

from fastapi import APIRouter, HTTPException
from database import emails_collection

# Create the router for email-related endpoints
router = APIRouter()


# ============================================
# ENDPOINT: GET /emails/{email}
# ============================================
# Purpose: Get all emails for a specific Gmail account
# Used when clicking on an account folder in the sidebar
@router.get("/{email}")
async def get_emails(email: str, folder: str = None):
    """
    Get emails for a specific Gmail account.
    Optionally filter by folder ("inbox" or "junk").
    Results are sorted by received_at (newest first).
    """
    # Build the query filter
    query = {"account_email": email}

    # If a folder filter is provided, add it to the query
    if folder and folder in ["inbox", "junk"]:
        query["folder"] = folder

    # Fetch emails from MongoDB, sorted by date (newest first)
    emails = emails_collection.find(query).sort("received_at", -1)

    # Convert to a list of dictionaries
    email_list = []
    for email_doc in emails:
        email_list.append({
            "id": str(email_doc["_id"]),
            "account_email": email_doc["account_email"],
            "gmail_id": email_doc["gmail_id"],
            "sender": email_doc.get("sender", "Unknown"),
            "subject": email_doc.get("subject", "(No Subject)"),
            "body": email_doc.get("body", ""),
            "received_at": email_doc.get("received_at", ""),
            "is_junk": email_doc.get("is_junk", False),
            "folder": email_doc.get("folder", "inbox"),
        })

    return {"emails": email_list, "count": len(email_list)}


# ============================================
# ENDPOINT: GET /emails/{email}/inbox
# ============================================
# Purpose: Get only inbox (non-junk) emails for an account
@router.get("/{email}/inbox")
async def get_inbox_emails(email: str):
    """Get only inbox emails for a specific account."""
    query = {"account_email": email, "folder": "inbox"}
    emails = emails_collection.find(query).sort("received_at", -1)

    email_list = []
    for email_doc in emails:
        email_list.append({
            "id": str(email_doc["_id"]),
            "account_email": email_doc["account_email"],
            "gmail_id": email_doc["gmail_id"],
            "sender": email_doc.get("sender", "Unknown"),
            "subject": email_doc.get("subject", "(No Subject)"),
            "body": email_doc.get("body", ""),
            "received_at": email_doc.get("received_at", ""),
            "is_junk": email_doc.get("is_junk", False),
            "folder": "inbox",
        })

    return {"emails": email_list, "count": len(email_list)}


# ============================================
# ENDPOINT: GET /emails/{email}/junk
# ============================================
# Purpose: Get only junk emails for an account
@router.get("/{email}/junk")
async def get_junk_emails(email: str):
    """Get only junk emails for a specific account."""
    query = {"account_email": email, "folder": "junk"}
    emails = emails_collection.find(query).sort("received_at", -1)

    email_list = []
    for email_doc in emails:
        email_list.append({
            "id": str(email_doc["_id"]),
            "account_email": email_doc["account_email"],
            "gmail_id": email_doc["gmail_id"],
            "sender": email_doc.get("sender", "Unknown"),
            "subject": email_doc.get("subject", "(No Subject)"),
            "body": email_doc.get("body", ""),
            "received_at": email_doc.get("received_at", ""),
            "is_junk": email_doc.get("is_junk", True),
            "folder": "junk",
        })

    return {"emails": email_list, "count": len(email_list)}


# ============================================
# ENDPOINT: GET /emails/{email}/message/{gmail_id}
# ============================================
# Purpose: Get a single email by its Gmail ID
# Used when clicking on an email to view its full content
@router.get("/{email}/message/{gmail_id}")
async def get_single_email(email: str, gmail_id: str):
    """Get a single email by its Gmail message ID."""
    email_doc = emails_collection.find_one({
        "account_email": email,
        "gmail_id": gmail_id,
    })

    if not email_doc:
        raise HTTPException(status_code=404, detail="Email not found")

    return {
        "id": str(email_doc["_id"]),
        "account_email": email_doc["account_email"],
        "gmail_id": email_doc["gmail_id"],
        "sender": email_doc.get("sender", "Unknown"),
        "subject": email_doc.get("subject", "(No Subject)"),
        "body": email_doc.get("body", ""),
        "received_at": email_doc.get("received_at", ""),
        "is_junk": email_doc.get("is_junk", False),
        "folder": email_doc.get("folder", "inbox"),
    }
