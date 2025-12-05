"""
Twilio SMS sender with multilingual fallback.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER")

def send_sms(message, to_number, lang="en"):
    """
    Send SMS in selected language. Falls back to file mock if Twilio not configured.
    """
    if TWILIO_SID and TWILIO_TOKEN and TWILIO_FROM:
        try:
            from twilio.rest import Client
            client = Client(TWILIO_SID, TWILIO_TOKEN)
            msg = client.messages.create(body=message, from_=TWILIO_FROM, to=to_number)
            return {"status":"sent","sid":msg.sid}
        except Exception as e:
            return {"status":"error","note":str(e)}
    else:
        # Fallback: save to alerts folder
        alerts_dir = Path("data/alerts")
        alerts_dir.mkdir(parents=True, exist_ok=True)
        fname = alerts_dir / f"mock_alert_{lang}.txt"
        with open(fname,"w",encoding="utf-8") as f:
            f.write(message)
        return {"status":"mock","path":str(fname)}

def send_twilio_sms(message, to_number=None):
    """
    Send SMS via Twilio. Returns (success: bool, message: str).
    Falls back to file mock if Twilio not configured.
    """
    if not to_number:
        to_number = os.getenv("TWILIO_TO_NUMBER", "+1234567890")  # Default mock number
    
    result = send_sms(message, to_number)
    if result.get("status") == "sent":
        return True, f"SMS sent successfully (SID: {result.get('sid', 'unknown')})"
    elif result.get("status") == "mock":
        return True, f"Mock SMS saved to {result.get('path', 'unknown')}"
    else:
        return False, result.get("note", "SMS sending failed")