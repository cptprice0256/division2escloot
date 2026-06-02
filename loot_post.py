import requests
import time
from datetime import datetime, timezone, timedelta
import os

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
JSON_URL = "https://cptprice0256.github.io/division2escloot/data/event/index.json"

def is_maintenance_window():
    # Tuesday 9:00 - 12:00 UTC+5:30 (adjust if your timezone differs)
    now = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    return now.weekday() == 1 and 9 <= now.hour < 12  # Tuesday = 1

def fetch_loot(max_retries=6):
    for attempt in range(1, max_retries + 1):
        try:
            cache_bust = int(time.time())
            url = f"{JSON_URL}?t={cache_bust}"
            print(f"📡 Attempt {attempt}/{max_retries} — Fetching JSON...")

            res = requests.get(url, headers={
                "User-Agent": "Mozilla/5.0",
                "Accept": "application/json",
                "Cache-Control": "no-cache"
            }, timeout=15)

            print(f"   HTTP {res.status_code}")

            if res.status_code != 200:
                print(f"⚠️ HTTP {res.status_code} — not ready yet.")
            elif res.text.strip().startswith("<"):
                print("⚠️ Got HTML instead of JSON. GitHub Pages not updated yet.")
            else:
                return res.json()

        except Exception as e:
            print(f"❌ Error on attempt {attempt}: {e}")

        if attempt < max_retries:
            print("⏳ Retrying in 2 minutes...")
            time.sleep(2 * 60)

    return None

def build_discord_payload(data):
    today = datetime.now(timezone(timedelta(hours=5, minutes=30)))
    today_iso = today.strftime("%Y-%m-%d")
    day_name = today.strftime("%A")

    print(f"📅 Looking for date: {today_iso}")

    today_entry = None
    active_week = None

    for week in data.get("Escalation", []):
        days = week.get("target_loot_by_day", [])
        if not days:
            continue
        day_names = ", ".join(d["day"] for d in days)
        print(f"  📅 Week {week['week']} | Days: {day_names}")

        found = next((d for d in days if str(d["day"]).strip() == today_iso), None)
        if found:
            today_entry = found
            active_week = week
            break

    if not active_week or not today_entry:
        print(f"⚠️ No loot data found for {today_iso}")
        return None, today_iso, day_name

    # Build mission lines
    mission_lines = ""
    for i, mission in enumerate(active_week.get("missions", [])):
        loot = today_entry.get("target_loot", [None] * (i + 1))[i] if today_entry.get("target_loot") and i < len(today_entry["target_loot"]) else "—"
        mission_lines += f"**{mission}**\n└ 🎯 {loot}\n\n"

    proto_gear = f"🟠 **{today_entry['prototype_gear_cache']}**" if today_entry.get("prototype_gear_cache") else "—"
    proto_weapon = f"🔫 **{today_entry['prototype_weapon_cache']}**" if today_entry.get("prototype_weapon_cache") else "—"

    description = (
        f"📋 **Week of {active_week['week']}**\n\n"
        f"{mission_lines}"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"🎁 **Prototype Gear Cache:** {proto_gear}\n"
        f"🔫 **Prototype Weapon Cache:** {proto_weapon}"
    )

    return description, today_iso, day_name

def post_to_discord(description, today_iso, day_name, found):
    embed_color = 16739840 if found else 8421504
    now_str = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%B %d, %Y %I:%M %p")

    if not found:
        description = "⚠️ No loot data found for today.\nDivision 2 may be under maintenance or the JSON hasn't been updated yet."

    payload = {
        "content": "🎯 **Division 2 — Daily Escalation Loot**",
        "embeds": [{
            "title": f"📅 {day_name}, {today_iso}",
            "description": description,
            "color": embed_color,
            "footer": {
                "text": f"Agent Intel Bot • Last Sync: {now_str}"
            }
        }]
    }

    res = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
    if res.status_code in (200, 204):
        print("✅ Discord message sent!")
    else:
        print(f"❌ Discord post failed: HTTP {res.status_code} — {res.text}")

def main():
    if is_maintenance_window():
        print("⏭️ Skipping — Division 2 maintenance window.")
        return

    data = fetch_loot()

    if data:
        description, today_iso, day_name = build_discord_payload(data)
        found = description is not None
    else:
        today = datetime.now(timezone(timedelta(hours=5, minutes=30)))
        today_iso = today.strftime("%Y-%m-%d")
        day_name = today.strftime("%A")
        description = None
        found = False

    post_to_discord(description, today_iso, day_name, found)

if __name__ == "__main__":
    main()
