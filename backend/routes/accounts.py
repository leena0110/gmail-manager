"""
routes/accounts.py — Account Management Routes
================================================
Handles listing and deleting Gmail accounts:
1. GET    /accounts/       → List all connected Gmail accounts with unread counts
2. DELETE /accounts/{email} → Remove a Gmail account
"""

from fastapi import APIRouter, HTTPException
from database import accounts_collection
from services.gmail_service import get_unread_count

# Create the router for account-related endpoints
router = APIRouter()

@router.get("/")
async def list_accounts():
    """
    Get all Gmail accounts that have been added.
    Returns email, added_at, and unread count for each account.
    """
    # Fetch all accounts from MongoDB
    accounts = accounts_collection.find({})

    # Convert to a list of dictionaries (safe for frontend)
    account_list = []
    for account in accounts:
        # Use cached unread count from the database (updated by background sync)
        unread_count = account.get("unread_count", 0)
        
        account_list.append({
            "id": str(account["_id"]),
            "email": account["email"],
            "added_at": account.get("added_at", ""),
            "unread_count": unread_count
        })

    return {"accounts": account_list}

@router.delete("/{email}")
async def delete_account(email: str):
    """
    Delete a Gmail account.
    This removes the account tokens from the database.
    """
    # Check if the account exists
    account = accounts_collection.find_one({"email": email})
    if not account:
        raise HTTPException(status_code=404, detail=f"Account {email} not found")

    # Delete the account itself
    accounts_collection.delete_one({"email": email})

    print(f"[OK] Deleted account {email}")

    return {
        "message": f"Account {email} deleted successfully",
    }
