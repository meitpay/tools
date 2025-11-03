import os
import time
import random
import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TOKEN or not CHAT_ID:
    raise ValueError("Missing TOKEN or CHAT_ID in .env file")

# Date range
YEAR = os.getenv("YEAR", "2025")
DAY = os.getenv("DAY", "24")
START_MONTH = os.getenv("START_MONTH", "8")
END_MONTH = os.getenv("END_MONTH", "9")

START = datetime(int(YEAR), int(START_MONTH), int(DAY), tzinfo=timezone.utc)
END = datetime(int(YEAR), int(END_MONTH), int(DAY), tzinfo=timezone.utc)

# API setup
url = (
    f"https://graph.microsoft.com/v1.0/chats/{CHAT_ID}/messages"
    "?$orderby=createdDateTime%20desc"
    f"&$filter=createdDateTime%20lt%20{END.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    "&$top=50"  # hard max :(
)
headers = {"Authorization": f"Bearer {TOKEN}"}

count = 0

def backoff(resp, attempt):
    """Handles exponential backoff with optional Retry-After header."""
    ra = resp.headers.get("Retry-After")
    sleep = int(ra) if ra and ra.isdigit() else min(60, 2**attempt) + random.uniform(0, 1)
    print(f"Backing off for {sleep:.1f}s (attempt {attempt})...")
    time.sleep(sleep)

attempt = 0
while url:
    resp = requests.get(url, headers=headers)
    if resp.status_code in (429, 503):
        attempt += 1
        backoff(resp, attempt)
        continue
    if not resp.ok:
        print("Request failed:", resp.status_code, resp.text)
        break

    attempt = 0
    data = resp.json()

    for m in data.get("value", []):
        dt = datetime.fromisoformat(m["createdDateTime"].replace("Z", "+00:00"))
        if START <= dt < END:
            count += 1
        elif dt < START:
            url = None
            break

    url = data.get("@odata.nextLink")

message_count = f"Messages from {START.strftime('%B %d')} to {END.strftime('%B %d, %Y')}: {count}."
print(message_count)
