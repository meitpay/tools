#!/usr/bin/env python3
import os, sys, json, time, requests
from dotenv import load_dotenv

load_dotenv()

TEAM_ID = os.getenv("TEAM_ID")
CHANNEL_ID = os.getenv("CHANNEL_ID")
TOKEN = os.getenv("GRAPH_ACCESS_TOKEN")  # Bearer token
GRAPH_BASE = os.getenv("GRAPH_BASE", "https://graph.microsoft.com/v1.0")
START_DATE_UTC = os.getenv("START_DATE_UTC", "2025-01-01T00:00:00.000Z")

OUTPUT_FILE = f"output/teams_alerts_messages.json"

def gget(url: str):
    """Makes a GET request to the Graph API with retry logic."""
    headers = {"Authorization": f"Bearer {TOKEN}", "Accept": "application/json"}
    delay = 1.0
    for i in range(6):
        try:
            r = requests.get(url, headers=headers, timeout=60)
            if r.status_code in (429, 500, 502, 503):
                retry_after = float(r.headers.get("Retry-After", delay))
                print(f"Request throttled or failed ({r.status_code}). Retrying in {retry_after:.1f}s...", file=sys.stderr)
                time.sleep(retry_after)
                delay = min(delay * 2, 30)
                continue
            r.raise_for_status()
            return r
        except requests.exceptions.RequestException as e:
            print(f"Request failed on attempt {i+1}: {e}", file=sys.stderr)
            time.sleep(delay)
            delay = min(delay * 2, 30)
    print("All retries failed. Exiting.", file=sys.stderr)
    sys.exit(1)

def list_all_messages(team_id: str, channel_id: str):
    """Fetches all available messages in the channel by following @odata.nextLink."""
    url = f"{GRAPH_BASE}/teams/{team_id}/channels/{channel_id}/messages/microsoft.graph.delta()?filter=lastModifiedDateTime gt {START_DATE_UTC}"
    out = []
    count = 0

    print("Fetching all messages (this may take a while)...")

    while url:
        r = gget(url)
        data = r.json()
        batch = data.get("value", [])
        out.extend(batch)
        count += len(batch)
        print(f"Fetched {len(batch)} messages (total so far: {count})")

        url = data.get("@odata.nextLink")

        if not url:
            print("No more pages left.")
            break

    print(f"✅ Finished fetching. Total messages collected: {len(out)}")
    return out

def parse_card(card: dict) -> dict:
    res = {
        "alertTitle": None, "messageTitle": None, "firedAt": None,
        "severity": None, "resource": None, "metricName": None,
        "metricValue": None, "threshold": None, "actions": []
    }
    def walk(n):
        if isinstance(n, dict):
            if n.get("type") == "TextBlock":
                t = (n.get("text") or "").strip()
                if t and not res["alertTitle"] and (n.get("size") in ("extraLarge","Large","large") or n.get("weight")=="bolder"):
                    res["alertTitle"] = t
                if   t.startswith("Fired at:"):     res["firedAt"]    = t.split(":",1)[1].strip()
                elif t.startswith("Severity:"):     res["severity"]   = t.split(":",1)[1].strip()
                elif t.startswith("Resource:"):     res["resource"]   = t.split(":",1)[1].strip()
                elif t.startswith("Metric name:"):  res["metricName"] = t.split(":",1)[1].strip()
                elif t.startswith("Metric value:"): res["metricValue"]= t.split(":",1)[1].strip()
                elif t.startswith("Threshold:"):    res["threshold"]  = t.split(":",1)[1].strip()
                else:
                    if not res["messageTitle"] and n.get("size") in ("medium","Large","large"):
                        res["messageTitle"] = t
            for k in ("items","columns","body"):
                v = n.get(k)
                if isinstance(v, list):
                    for c in v: walk(c)
        elif isinstance(n, list):
            for c in n: walk(c)
    walk(card.get("body", []))
    for a in card.get("actions", []) or []:
        if (a.get("type") or "").lower().endswith("openurl"):
            res["actions"].append({"title": a.get("title"), "url": a.get("url")})
    return res

def extract_from_message(m: dict):
    created = m.get("createdDateTime")
    fr = m.get("from") or {}
    user = fr.get("user") or fr.get("application") or {}
    sender = user.get("displayName") or user.get("id") or "Unknown"
    mid = m.get("id")
    out = []
    for att in (m.get("attachments") or []):
        if att.get("contentType") == "application/vnd.microsoft.card.adaptive" and att.get("content"):
            try:
                card = json.loads(att["content"])
            except Exception:
                continue
            out.append({
                "messageId": mid,
                "createdDateTime": created,
                "sender": sender,
                "card": parse_card(card),
            })
    return out

def main():
    if not (TEAM_ID and CHANNEL_ID and TOKEN):
        print("Please set TEAM_ID, CHANNEL_ID, and GRAPH_ACCESS_TOKEN in your .env.", file=sys.stderr)
        sys.exit(1)

    messages = list_all_messages(TEAM_ID, CHANNEL_ID)
    messages.reverse()  # Optional: oldest first

    results = []
    for m in messages:
        results.extend(extract_from_message(m))

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(results)} alerts written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
