"""
routes/emails.py — Email Retrieval Routes
==========================================
Handles fetching emails from Gmail API:
1. GET /emails/{email}         → Get all emails for an account
2. GET /emails/{email}/inbox   → Get only inbox emails
3. GET /emails/{email}/junk    → Get only junk emails
4. GET /emails/{email}/sent    → Get only sent emails
5. GET /emails/{email}/message/{gmail_id} → Get a single email by Gmail ID
6. POST /emails/{email}/send   → Send an email
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import accounts_collection
from services.gmail_service import fetch_emails_from_gmail, get_single_email_from_gmail, send_email, mark_as_read
from services.sync_service import sync_all_accounts

router = APIRouter()

@router.post("/sync")
async def trigger_manual_sync():
    """Manually trigger the background sync logic for all accounts."""
    try:
        await sync_all_accounts()
        return {"message": "Sync triggered successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class SendEmailRequest(BaseModel):
    to: str
    subject: str
    body: str
    attachments: list = None
    cc: str = None
    bcc: str = None

def get_account(email: str):
    account = accounts_collection.find_one({"email": email})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.get("/{email}")
async def get_emails(email: str, folder: str = "inbox"):
    account = get_account(email)
    emails = fetch_emails_from_gmail(account, folder=folder)
    return {"emails": emails, "count": len(emails)}

@router.get("/{email}/inbox")
async def get_inbox_emails(email: str):
    account = get_account(email)
    emails = fetch_emails_from_gmail(account, folder="inbox")
    return {"emails": emails, "count": len(emails)}

@router.get("/{email}/junk")
async def get_junk_emails(email: str):
    account = get_account(email)
    emails = fetch_emails_from_gmail(account, folder="junk")
    return {"emails": emails, "count": len(emails)}

@router.get("/{email}/sent")
async def get_sent_emails(email: str):
    account = get_account(email)
    emails = fetch_emails_from_gmail(account, folder="sent")
    return {"emails": emails, "count": len(emails)}

@router.get("/{email}/message/{gmail_id}")
async def get_single_email(email: str, gmail_id: str):
    account = get_account(email)
    email_data = get_single_email_from_gmail(account, gmail_id)
    if not email_data:
        raise HTTPException(status_code=404, detail="Email not found")
    return email_data

@router.post("/{email}/read/{gmail_id}")
async def mark_email_read(email: str, gmail_id: str):
    account = get_account(email)
    success = mark_as_read(account, gmail_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to mark email as read")
    return {"status": "success"}


@router.post("/{email}/send")
async def send_new_email(email: str, request: SendEmailRequest):
    account = get_account(email)
    success = send_email(
        account, 
        request.to, 
        request.subject, 
        request.body, 
        request.attachments,
        cc=request.cc,
        bcc=request.bcc
    )
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send email")
    return {"status": "success", "message": "Email sent"}
