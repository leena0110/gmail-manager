"""
services/ai_service.py — AI Junk Mail Classification
======================================================
Uses Gemini API to classify emails as "inbox" or "junk".

How it works:
1. We send the email's sender, subject, and body to Gemini
2. Gemini analyzes the content and determines if it's junk
3. Returns a simple True/False result

Junk criteria (for Gemini):
- Spam, phishing, scam emails
- Unsolicited marketing/promotional emails
- Newsletters the user didn't sign up for
- Suspicious or misleading content
"""

import os
from google import genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the Gemini client with our API key
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))


def classify_email(sender: str, subject: str, body: str) -> bool:
    """
    Use Gemini AI to classify an email as junk or not.
    
    Args:
        sender:  The email sender (From field)
        subject: The email subject line
        body:    The email body content (plain text)
    
    Returns:
        True if the email is junk/spam, False if it's legitimate
    """
    try:
        # Truncate the body to avoid sending too much text
        # (saves API costs and stays within token limits)
        truncated_body = body[:2000] if body else "(empty)"

        # --- Build the prompt for Gemini ---
        prompt = f"""You are an email junk/spam classifier. Analyze the following email and determine if it is junk mail.

Junk mail includes:
- Spam and unsolicited bulk email
- Phishing attempts or scam emails  
- Unsolicited marketing or promotional emails
- Suspicious emails with misleading subject lines
- Newsletter spam

Legitimate mail includes:
- Personal emails from real people
- Important notifications (bank, school, work)
- Emails the user likely signed up for
- Transactional emails (receipts, confirmations, shipping)
- Calendar invitations
- Emails from known services the user uses

EMAIL TO CLASSIFY:
From: {sender}
Subject: {subject}
Body: {truncated_body}

Respond with ONLY one word: "junk" or "inbox". Nothing else."""

        # --- Send to Gemini API ---
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )

        # --- Parse Gemini's response ---
        result = response.text.strip().lower()

        # Check if Gemini said "junk"
        is_junk = "junk" in result

        classification = "JUNK 🚫" if is_junk else "INBOX ✅"
        print(f"   🤖 AI classified: {subject[:50]}... → {classification}")

        return is_junk

    except Exception as e:
        print(f"❌ AI classification error: {e}")
        # If AI fails, default to inbox (don't accidentally hide important emails)
        return False
