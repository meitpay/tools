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

print("Starting Message Counter Script")
print(f"CHAT_ID={CHAT_ID}")

if not TOKEN or not CHAT_ID:
    raise ValueError("Missing TOKEN or CHAT_ID in .env file")

# Date range
# YEAR = os.getenv("YEAR", "2025")
START_YEAR = os.getenv("START_YEAR")
END_YEAR = os.getenv("END_YEAR")
DAY = os.getenv("DAY")
START_MONTH = os.getenv("START_MONTH")
END_MONTH = os.getenv("END_MONTH")

missing_dates = [
    name
    for name, value in {
        "START_YEAR": START_YEAR,
        "END_YEAR": END_YEAR,
        "DAY": DAY,
        "START_MONTH": START_MONTH,
        "END_MONTH": END_MONTH,
    }.items()
    if not value
]
if missing_dates:
    raise ValueError(f"Missing date config in .env: {', '.join(missing_dates)}")

try:
    start_year = int(START_YEAR)
    end_year = int(END_YEAR)
    day = int(DAY)
    start_month = int(START_MONTH)
    end_month = int(END_MONTH)
except ValueError as exc:
    raise ValueError(
        "Date config must be numeric: START_YEAR, END_YEAR, DAY, START_MONTH, END_MONTH"
    ) from exc

if not (1 <= start_month <= 12 and 1 <= end_month <= 12):
    raise ValueError("START_MONTH and END_MONTH must be in 1..12")
if not (1 <= day <= 31):
    raise ValueError("DAY must be in 1..31")
if start_year <= 0 or end_year <= 0:
    raise ValueError("START_YEAR and END_YEAR must be positive")

START = datetime(start_year, start_month, day, tzinfo=timezone.utc)
END = datetime(end_year, end_month, day, tzinfo=timezone.utc)
print(f"Counting messages from {START.isoformat()} to {END.isoformat()} (UTC)")

# API setup
url = (
    f"https://graph.microsoft.com/v1.0/chats/{CHAT_ID}/messages"
    "?$orderby=createdDateTime%20desc"
    f"&$filter=createdDateTime%20lt%20{END.strftime('%Y-%m-%dT%H:%M:%SZ')}"
    "&$top=50"  # hard max :(
)
headers = {"Authorization": f"Bearer {TOKEN}"}

count = 0
page = 0

def backoff(resp, attempt):
    """Handles exponential backoff with optional Retry-After header."""
    ra = resp.headers.get("Retry-After")
    sleep = int(ra) if ra and ra.isdigit() else min(60, 2**attempt) + random.uniform(0, 1)
    print(f"Backing off for {sleep:.1f}s (attempt {attempt})...")
    time.sleep(sleep)

attempt = 0
while url:
    page += 1
    print(f"Requesting page {page}: {url}")
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
    batch = 0

    for m in data.get("value", []):
        dt = datetime.fromisoformat(m["createdDateTime"].replace("Z", "+00:00"))
        if START <= dt < END:
            count += 1
            batch += 1
        elif dt < START:
            url = None
            break
    print(f"Page {page}: counted {batch} messages (running total: {count})")

    url = data.get("@odata.nextLink")
    if url:
        print("Next page detected.")

message_count = f"Messages from {START.strftime('%B %d')} to {END.strftime('%B %d, %Y')}: {count}."
print(message_count)
