"""
main.py — FastAPI Application Entry Point
==========================================
This is the main file that starts the Gmail Manager backend.
It sets up the FastAPI app, registers all route handlers,
and configures CORS for frontend communication.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import our route modules
from routes.auth import router as auth_router
from routes.accounts import router as accounts_router
from routes.emails import router as emails_router

# --- Create the FastAPI app ---
app = FastAPI(
    title="Gmail Manager API",
    description="Manage multiple Gmail accounts",
    version="1.0.0",
)

# --- CORS Configuration ---
# This allows our React frontend (on port 5173) to talk to the backend (on port 8000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

# --- Register Route Handlers ---
# Each router handles a group of related endpoints
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])
app.include_router(emails_router, prefix="/emails", tags=["Emails"])


from services.sync_service import start_sync_loop

# --- Startup and Shutdown Events ---
@app.on_event("startup")
async def startup_event():
    """Start background sync when the server starts."""
    import asyncio
    # Run the sync loop in the background task
    asyncio.create_task(start_sync_loop())

# --- Health Check Endpoint ---
@app.get("/")
async def root():
    """Simple health check to verify the server is running."""
    return {"message": "Gmail Manager API is running!", "status": "healthy"}
