## sources.py
```python
import requests
from typing import List, Dict

HN_TOP_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{id}.json"


def fetch_hn_top(limit: int = 5) -> List[Dict]:
    try:
        ids = requests.get(HN_TOP_URL, timeout=15).json()[:limit]
        items = []
        for i in ids:
            data = requests.get(HN_ITEM_URL.format(id=i), timeout=15).json()
            if not data:
                continue
            title = data.get("title", "(no title)")
            url = data.get("url")
            # Some HN posts are Ask/Show with no URL — link to HN discussion
            if not url:
                url = f"https://news.ycombinator.com/item?id={data.get('id')}"
            items.append({
                "title": title,
                "url": url,
                "source": "Hacker News",
            })
        return items
    except Exception:
        return []


# Optional RSS support (simple)
try:
    import feedparser  # type: ignore
except Exception:
    feedparser = None


def fetch_rss_items(feeds: List[str], max_per_feed: int = 2) -> List[Dict]:
    if not feedparser:
        return []
    out: List[Dict] = []
    for url in feeds:
        try:
            d = feedparser.parse(url)
            for entry in d.entries[:max_per_feed]:
                title = entry.get("title") or "(no title)"
                link = entry.get("link")
                source = d.feed.get("title") or url
                out.append({"title": title, "url": link, "source": source})
        except Exception:
            continue
    return out
