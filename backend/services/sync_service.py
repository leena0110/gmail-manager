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
from services.gmail_service import fetch_emails_for_account
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

    print(f"🔄 Background sync started (checking every {SYNC_INTERVAL}s)")

    while _sync_running:
        try:
            await sync_all_accounts()
        except Exception as e:
            print(f"❌ Sync loop error: {e}")

        # Wait before checking again
        await asyncio.sleep(SYNC_INTERVAL)


async def stop_sync_loop():
    """Stop the background sync loop gracefully."""
    global _sync_running
    _sync_running = False
    print("🛑 Background sync stopped")


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
    print(f"🔄 Syncing {len(accounts)} account(s)... [{datetime.utcnow().strftime('%H:%M:%S')}]")
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
    print(f"\n📧 Syncing: {email_address}")

    # --- Step 1: Fetch new emails from Gmail ---
    # This runs in a thread pool because it makes HTTP calls (blocking I/O)
    loop = asyncio.get_event_loop()
    new_emails = await loop.run_in_executor(
        None,
        fetch_emails_for_account,
        account,
    )

    if not new_emails:
        print(f"   ✅ No new emails for {email_address}")
        return

    print(f"   📨 Processing {len(new_emails)} new email(s)...")

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

            # Add classification results to the email data
            email_data["is_junk"] = is_junk
            email_data["folder"] = "junk" if is_junk else "inbox"

            # Save to MongoDB (upsert to avoid duplicates)
            emails_collection.update_one(
                {
                    "gmail_id": email_data["gmail_id"],
                    "account_email": email_data["account_email"],
                },
                {"$set": email_data},
                upsert=True,
            )

            folder_label = "🚫 Junk" if is_junk else "✅ Inbox"
            print(f"   💾 Saved: {email_data['subject'][:40]}... → {folder_label}")

        except Exception as e:
            print(f"   ❌ Error processing email {email_data.get('gmail_id')}: {e}")

    print(f"   ✅ Sync complete for {email_address}")
