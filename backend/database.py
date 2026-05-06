"""
database.py — MongoDB Connection Module
========================================
This file handles connecting to MongoDB Atlas.
It provides access to the 'accounts' and 'emails' collections
used throughout the application.
"""

import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- Connect to MongoDB Atlas ---
# The connection string comes from our .env file
MONGODB_URI = os.getenv("MONGODB_URI")

# Create a MongoDB client (this connects to the cloud database)
client = MongoClient(MONGODB_URI)

# Select (or create) a database called "gmail_manager"
db = client["gmail_manager"]

# --- Define our two collections ---

# 'accounts' collection: stores Gmail account info and OAuth tokens
accounts_collection = db["accounts"]

# 'emails' collection: stores fetched emails with junk classification
emails_collection = db["emails"]

# Create an index on gmail_id to avoid duplicate emails
emails_collection.create_index("gmail_id", unique=True)

# Create an index on account_email for fast lookups
emails_collection.create_index("account_email")

print("✅ Connected to MongoDB Atlas successfully!")
