import requests
import os
from datetime import datetime, timezone

DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
JSON_URL = "https://cptprice0256.github.io/division2escloot/data/event/index.json"

GEAR_EMOJI = {
    "backpack": "🎒",
    "chest"   : "🧥",
    "gloves"  : "🟡",
    "holster" : "🔵",
    "kneepads": "🟠",
    "mask"    : "😷",
}

WEAPON_EMOJI = {
    "pistol"  : "🔫",
    "rifle"   : "🔫",
    "ar"      : "🔫",
    "lmg"     : "🔫",
    "smg"     : "🔫",
    "shotgun" : "🔫",
    "sniper"  : "🔫",
    "marksman": "🔫",
}

def get_gear_emoji(cache_type):
    return GEAR_EMOJI.get(cache_type.lower().strip(), "🎁")

def get_weapon_emoji(cache_type):
    return WEAPON_EMOJI.get(cache_type.lower().strip(), "🔫")

def fetch_json():
    response = requests.get(JSON_URL, timeout=15)
    response.raise_for_status()
    return response.json()

def get_today_loot(data):
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    print(f"🗓️ Looking for date: {today}")

    for week_block in data.get("Escalation", []):
        week_start = week_block.get("week", "")
        missions   = week_block.get("missions", [])

        for day_block in week_block.get("target_loot_by_day", []):
            if day_block.get("day") == today:
                return {
                    "today"                 : today,
                    "week"                  : week_start,
                    "missions"              : missions,
                    "target_loot"           : day_block.get("target_loot", []),
                    "prototype_gear_cache"  : day_block.get("prototype_gear_cache", "N/A"),
                    "prototype_weapon_cache": day_block.get("prototype_weapon_cache", "N/A"),
                }

    return None

def format_day(date_str):
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    return dt.strftime("%A, %Y-%m-%d")  # e.g. Monday, 2026-06-02

def format_sync_time(dt):
    # e.g. 6/2/2026, 1:45:29 PM
    month = dt.month
    day   = dt.day
    year  = dt.year
    time  = dt.strftime("%I:%M:%S %p").lstrip("0")
    return f"{month}/{day}/{year}, {time}"

def build_embed(loot):
    now = datetime.now(timezone.utc)

    day_label    = format_day(loot["today"])
    week_label   = loot["week"]
    sync_time    = format_sync_time(now)
    missions     = loot["missions"]
    target_loot  = loot["target_loot"]
    gear_cache   = loot["prototype_gear_cache"]
    weapon_cache = loot["prototype_weapon_cache"]
    gear_emoji   = get_gear_emoji(gear_cache)
    weapon_emoji = get_weapon_emoji(weapon_cache)

    # --- Build embed description ---
    lines = []

    # Date and week
    lines.append(f"📅 **{day_label}**")
    lines.append(f"📋 **Week of {week_label}**")
    lines.append("")  # blank line

    # Mission + loot pairs
    for i, mission in enumerate(missions):
        loot_item = target_loot[i] if i < len(target_loot) else "N/A"
        lines.append(f"**{mission}**")
        lines.append(f"└ 🎯 {loot_item}")
        lines.append("")  # blank line between pairs

    # Divider
    lines.append("———————————————————")

    # Prototype caches
    lines.append(f"🎁 **Prototype Gear Cache:** {gear_emoji} {gear_cache}")
    lines.append(f"🔫 **Prototype Weapon Cache:** {weapon_emoji} {weapon_cache}")

    description = "\n".join(lines)

    embed = {
        "title"      : "🎯 Division 2 — Daily Escalation Loot",
        "description": description,
        "color"      : 0xF0A500,   # golden yellow — matches the left border in screenshot
        "footer"     : {
            "text": f"Agent Intel Bot • Last Sync: {sync_time}"
        }
    }

    return embed

def post_to_discord(embed):
    payload  = {"embeds": [embed]}
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
        fallback_embed = {
            "title"      : "🎯 Division 2 — Daily Escalation Loot",
            "description": "⚠️ No loot data found for today.",
            "color"      : 0xF0A500,
            "footer"     : {"text": "Agent Intel Bot"}
        }
        post_to_discord(fallback_embed)
        return

    embed = build_embed(loot)
    print("📨 Sending to Discord...")
    post_to_discord(embed)

if __name__ == "__main__":
    main()
