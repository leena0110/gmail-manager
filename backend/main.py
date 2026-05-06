"""
main.py — FastAPI Application Entry Point
==========================================
This is the main file that starts the Gmail Manager backend.
It sets up the FastAPI app, registers all route handlers,
configures CORS for frontend communication, and starts
the background email sync job.
"""

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import our route modules
from routes.auth import router as auth_router
from routes.accounts import router as accounts_router
from routes.emails import router as emails_router

# Import the background sync service
from services.sync_service import start_sync_loop, stop_sync_loop


# --- Lifespan: runs code on startup and shutdown ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    This runs when the server starts up and shuts down.
    On startup: we begin the background email sync loop.
    On shutdown: we cleanly stop the sync loop.
    """
    print("🚀 Gmail Manager backend starting up...")
    
    # Start the background task that fetches emails every 30 seconds
    sync_task = asyncio.create_task(start_sync_loop())
    
    yield  # The app is running between these two points
    
    # Shutdown: stop the sync loop
    print("🛑 Shutting down background sync...")
    await stop_sync_loop()
    sync_task.cancel()


# --- Create the FastAPI app ---
app = FastAPI(
    title="Gmail Manager API",
    description="Manage multiple Gmail accounts with AI-powered junk detection",
    version="1.0.0",
    lifespan=lifespan,
)

# --- CORS Configuration ---
# This allows our React frontend (on port 5173) to talk to the backend (on port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# --- Register Route Handlers ---
# Each router handles a group of related endpoints
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])
app.include_router(emails_router, prefix="/emails", tags=["Emails"])


# --- Health Check Endpoint ---
@app.get("/")
async def root():
    """Simple health check to verify the server is running."""
    return {"message": "Gmail Manager API is running!", "status": "healthy"}
