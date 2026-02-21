import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import feedparser


def fetch_single_rss(url: str, since_days: int = 1) -> List[Dict[str, Any]]:
    """
    Blocking function to fetch and parse a single RSS feed.
    """
    all_entries = []
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=since_days)

    # feedparser.parse is a blocking network call
    feed_data: Any = feedparser.parse(url)
    feed_info = feed_data.get("feed", {})
    feed_title = feed_info.get("title", "Unknown Feed")
    entries = feed_data.get("entries", [])

    for entry in entries:
        published_parsed = entry.get("published_parsed") or entry.get("updated_parsed")
        published_dt: datetime | None = None

        if published_parsed:
            timestamp = time.mktime(published_parsed)
            published_dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)

        # Include if it's within the time window OR if it has no date (to be safe)
        if (published_dt and published_dt >= cutoff_date) or not published_parsed:
            all_entries.append(
                {
                    "title": entry.get("title", "No Title"),
                    "link": entry.get("link", ""),
                    "summary": entry.get("summary", ""),
                    "published": published_dt.isoformat() if published_dt else "Unknown",
                    "feed_title": feed_title,
                }
            )

    return all_entries
