import os
import textwrap
from datetime import datetime, timezone
from sources import fetch_hn_top, fetch_rss_items
import requests

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
CUSTOM_TITLE = os.environ.get("CUSTOM_TITLE", "Weekly Roundup ")
RSS_FEEDS = [u.strip() for u in os.environ.get("RSS_FEEDS", "").split(",") if u.strip()]
MAX_ITEMS = int(os.environ.get("MAX_ITEMS", 5))

TG_SEND_URL = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"


def fmt_item(idx, title, url, source):
    # Escape markdown special chars for Telegram MarkdownV2
    def esc(s: str) -> str:
        for ch in "_[]()~`>#+-=|{}.!":
            s = s.replace(ch, f"\\{ch}")
        return s
    t = esc(title)
    u = esc(url) if url else ""
    s = esc(source) if source else ""
    if u:
        return f"{idx}. [{t}]({u}) _({s})_"
    else:
        return f"{idx}. {t} _({s})_"


def build_message():
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    headline = f"*{CUSTOM_TITLE.strip()} — {date_str}*\n"

    items = []
    # Hacker News Top
    items.extend(fetch_hn_top(limit=MAX_ITEMS))

    # Optional: RSS feeds
    if RSS_FEEDS:
        rss_items = fetch_rss_items(RSS_FEEDS, max_per_feed=2)
        items.extend(rss_items)

    # Deduplicate by URL/title
    seen = set()
    deduped = []
    for it in items:
        key = (it.get("url") or it.get("title"))
        if key and key not in seen:
            seen.add(key)
            deduped.append(it)

    if not deduped:
        return headline + "No items found this week."

    lines = [fmt_item(i+1, it["title"], it.get("url"), it.get("source", "")) for i, it in enumerate(deduped[:MAX_ITEMS])]
    footer = textwrap.dedent(
        """
        \n_Reply with ideas for next week or DM me to add feeds._
        """
    ).strip()

    return headline + "\n".join(lines) + "\n\n" + footer


def send_message(text: str):
    if not TELEGRAM_TOKEN or not CHAT_ID:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID env vars.")

    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "MarkdownV2",
        "disable_web_page_preview": True,
    }
    r = requests.post(TG_SEND_URL, json=payload, timeout=20)
    r.raise_for_status()
    return r.json()


if __name__ == "__main__":
    msg = build_message()
    print("\n===== MESSAGE PREVIEW =====\n")
    print(msg)

    # To do a dry run (no send), set DRY_RUN=1 in the environment
    if os.environ.get("DRY_RUN") == "1":
        print("\n(DRY RUN) — not sending to Telegram.")
    else:
        resp = send_message(msg)
        print("\nSent:", resp.get("ok", False))
