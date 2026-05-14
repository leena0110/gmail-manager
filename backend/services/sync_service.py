"""
services/sync_service.py — Background Sync Service (Pure Client Model)
=====================================================================
In the Pure Client model, we do NOT save any email data to the database.
This service simply runs in the background to update the unread counts 
so the sidebar stays up to date.
"""

import asyncio
from datetime import datetime
from database import accounts_collection
from services.gmail_service import get_gmail_service, get_unread_count

# How often to check for updates (in seconds)
SYNC_INTERVAL = 30
_sync_running = True

async def start_sync_loop():
    """Main sync loop that runs in the background."""
    global _sync_running
    _sync_running = True
    print(f"[SYNC] Pure Client sync started (Heartbeat every {SYNC_INTERVAL}s)")

    while _sync_running:
        try:
            await sync_all_accounts()
        except Exception as e:
            print(f"[ERROR] Sync loop error: {e}")
        await asyncio.sleep(SYNC_INTERVAL)

async def stop_sync_loop():
    """Stop the background sync loop."""
    global _sync_running
    _sync_running = False
    print("[STOP] Background sync stopped")

async def sync_all_accounts():
    """Update metadata for all accounts."""
    accounts = list(accounts_collection.find({}))
    if not accounts:
        return

    for account in accounts:
        try:
            # Simply fetch the live unread count and update the account metadata
            unread_count = get_unread_count(account)
            accounts_collection.update_one(
                {"email": account["email"]},
                {"$set": {
                    "unread_count": unread_count,
                    "last_sync": datetime.utcnow()
                }}
            )
            # print(f"   [SYNC] {account['email']}: {unread_count} unread")
        except Exception as e:
            print(f"   [ERROR] Failed to sync metadata for {account['email']}: {e}")
