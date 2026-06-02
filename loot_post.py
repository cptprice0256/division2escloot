import requests
import os
from datetime import datetime, timezone

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
JSON_URL = "https://cptprice0256.github.io/division2escloot/data/event/index.json"

def fetch_json():
    response = requests.get(JSON_URL, timeout=15)
    response.raise_for_status()
    return response.json()

def get_today_loot(data):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"🗓️ Looking for date: {today}")

    escalation_list = data.get("Escalation", [])

    for week_block in escalation_list:
        # ✅ Check weekly missions (week start date matches today's week)
        week_start = week_block.get("week", "")
        missions = week_block.get("missions", [])

        # ✅ Find today's daily loot
        for day_block in week_block.get("target_loot_by_day", []):
            if day_block.get("day") == today:
                return {
                    "week": week_start,
                    "missions": missions,
                    "target_loot": day_block.get("target_loot", []),
                    "prototype_gear_cache": day_block.get("prototype_gear_cache", "N/A"),
                    "prototype_weapon_cache": day_block.get("prototype_weapon_cache", "N/A")
                }

    return None

def build_discord_message(loot):
    missions = "\n".join(f"• {m}" for m in loot["missions"])
    target_loot = "\n".join(f"• {t}" for t in loot["target_loot"])

    message = f"""🎮 **The Division 2 — Daily Loot** `{loot['week']} week`

🗺️ **Escalation Missions**
{missions}

🎯 **Target Loot Today**
{target_loot}

🎒 **Prototype Gear Cache:** {loot['prototype_gear_cache'].capitalize()}
🔫 **Prototype Weapon Cache:** {loot['prototype_weapon_cache'].capitalize()}
"""
    return message

def post_to_discord(message):
    payload = {"content": message}
    response = requests.post(DISCORD_WEBHOOK, json=payload, timeout=15)
    if response.status_code in (200, 204):
        print("✅ Posted to Discord successfully!")
    else:
        print(f"❌ Discord post failed: {response.status_code} — {response.text}")

def main():
    print("📦 Fetching JSON...")
    data = fetch_json()

    loot = get_today_loot(data)

    if not loot:
        print("⚠️ No loot data found for today.")
        post_to_discord("⚠️ No Division 2 loot data found for today.")
        return

    message = build_discord_message(loot)
    print("📨 Sending to Discord...")
    print(message)
    post_to_discord(message)

if __name__ == "__main__":
    main()
