"""
services/sync_service.py — Background Email Sync Service
==========================================================
This service runs in the background while the server is active.
Every 30 seconds, it:
1. Loops through all connected Gmail accounts
2. Fetches any new emails from each account
3. Classifies each new email as inbox or junk using Claude AI
4. Saves the classified emails to MongoDB

This is what gives the app its "real-time" feel — new emails
appear automatically without the user having to refresh.
"""

import asyncio
from datetime import datetime

from database import accounts_collection, emails_collection
from services.gmail_service import fetch_emails_from_gmail
from services.ai_service import classify_email

# How often to check for new emails (in seconds)
SYNC_INTERVAL = 30

# Flag to control the sync loop (set to False to stop it)
_sync_running = True


async def start_sync_loop():
    """
    Main sync loop that runs continuously in the background.
    Checks all accounts for new emails every SYNC_INTERVAL seconds.
    """
    global _sync_running
    _sync_running = True

    print(f"[SYNC] Background sync started (checking every {SYNC_INTERVAL}s)")

    while _sync_running:
        try:
            await sync_all_accounts()
        except Exception as e:
            print(f"[ERROR] Sync loop error: {e}")

        # Wait before checking again
        await asyncio.sleep(SYNC_INTERVAL)


async def stop_sync_loop():
    """Stop the background sync loop gracefully."""
    global _sync_running
    _sync_running = False
    print("[STOP] Background sync stopped")


async def sync_all_accounts():
    """
    Sync emails for ALL connected Gmail accounts.
    This is called every 30 seconds by the sync loop.
    """
    # Get all accounts from MongoDB
    accounts = list(accounts_collection.find({}))

    if not accounts:
        return  # No accounts to sync, skip silently

    print(f"\n{'='*50}")
    print(f"[SYNC] Syncing {len(accounts)} account(s)... [{datetime.utcnow().strftime('%H:%M:%S')}]")
    print(f"{'='*50}")

    for account in accounts:
        await sync_single_account(account)


async def sync_single_account(account):
    """
    Sync emails for a single Gmail account.
    
    Steps:
    1. Fetch new emails from Gmail API
    2. Classify each email with Claude AI
    3. Save to MongoDB with the classification result
    
    Args:
        account: MongoDB document with account info and tokens
    """
    email_address = account["email"]
    print(f"\n[SYNC] Syncing: {email_address}")

    # --- Step 1: Fetch new emails from Gmail ---
    # This runs in a thread pool because it makes HTTP calls (blocking I/O)
    loop = asyncio.get_event_loop()
    new_emails = await loop.run_in_executor(
        None,
        fetch_emails_from_gmail,
        account,
    )

    if not new_emails:
        print(f"   [OK] No new emails for {email_address}")
        return

    print(f"   [INFO] Processing {len(new_emails)} new email(s)...")

    # --- Step 2 & 3: Classify each email and save to MongoDB ---
    for email_data in new_emails:
        try:
            # Classify with Claude AI (run in thread pool)
            is_junk = await loop.run_in_executor(
                None,
                classify_email,
                email_data["sender"],
                email_data["subject"],
                email_data["body"],
            )

            # Determine the correct folder based on Gmail labels
            labels = email_data.get("labelIds", [])
            if "SENT" in labels:
                email_data["folder"] = "sent"
            elif is_junk or "SPAM" in labels:
                email_data["folder"] = "junk"
            else:
                email_data["folder"] = "inbox"

            # Save to MongoDB (upsert to avoid duplicates)
            emails_collection.update_one(
                {
                    "gmail_id": email_data["gmail_id"],
                    "account_email": email_data["account_email"],
                },
                {"$set": email_data},
                upsert=True,
            )

            folder_label = "JUNK" if is_junk else "INBOX"
            print(f"   [SAVED] {email_data['subject'][:40]}... -> {folder_label}")

        except Exception as e:
            print(f"   [ERROR] Error processing email {email_data.get('gmail_id')}: {e}")

    # --- Step 4: Update unread count for the account ---
    from services.gmail_service import get_unread_count
    unread_count = get_unread_count(account)
    accounts_collection.update_one(
        {"email": email_address},
        {"$set": {"unread_count": unread_count}}
    )

    print(f"   [OK] Sync complete for {email_address} (Unread: {unread_count})")
