"""
routes/accounts.py — Account Management Routes
================================================
Handles listing and deleting Gmail accounts:
1. GET    /accounts/       → List all connected Gmail accounts
2. DELETE /accounts/{email} → Remove a Gmail account and its emails
"""

from fastapi import APIRouter, HTTPException
from database import accounts_collection, emails_collection

# Create the router for account-related endpoints
router = APIRouter()


# ============================================
# ENDPOINT: GET /accounts/
# ============================================
# Purpose: Return a list of all connected Gmail accounts
# The frontend sidebar uses this to show account folders
@router.get("/")
async def list_accounts():
    """
    Get all Gmail accounts that have been added.
    Returns email and added_at for each account (no tokens!).
    """
    # Fetch all accounts from MongoDB
    accounts = accounts_collection.find({})

    # Convert to a list of dictionaries (safe for frontend)
    account_list = []
    for account in accounts:
        account_list.append({
            "id": str(account["_id"]),          # Convert ObjectId to string
            "email": account["email"],
            "added_at": account.get("added_at", ""),
        })

    return {"accounts": account_list}


# ============================================
# ENDPOINT: DELETE /accounts/{email}
# ============================================
# Purpose: Remove a Gmail account and all its emails
# Called when the user wants to disconnect a Gmail account
@router.delete("/{email}")
async def delete_account(email: str):
    """
    Delete a Gmail account and all associated emails.
    This removes the account tokens AND all fetched emails for that account.
    """
    # Check if the account exists
    account = accounts_collection.find_one({"email": email})
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {email} not found")

    # Delete all emails belonging to this account
    deleted_emails = emails_collection.delete_many({"account_email": email})

    # Delete the account itself
    accounts_collection.delete_one({"email": email})

    print(f"🗑️ Deleted account {email} and {deleted_emails.deleted_count} emails")

    return {
        "message": f"Account {email} deleted successfully",
        "emails_deleted": deleted_emails.deleted_count,
    }
