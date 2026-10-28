#!/usr/bin/env python3
"""Fetch a daily Nizamabad news digest from Google News RSS."""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "local-news.json"
QUERY = 'Nizamabad Telangana district'
FEED_URL = "https://news.google.com/rss/search?q=" + quote(QUERY) + "&hl=en-IN&gl=IN&ceid=IN:en"

def clean(value):
    return re.sub(r"\s+", " ", (value or "")).strip()

def main():
    request = urllib.request.Request(
        FEED_URL,
        headers={"User-Agent": "TASVIA-Academy-Local-News/1.0 (daily headline digest)"}
    )
    with urllib.request.urlopen(request, timeout=25) as response:
        xml_data = response.read()
    root = ET.fromstring(xml_data)
    channel = root.find("channel")
    if channel is None:
        raise RuntimeError("RSS feed did not contain a channel")
    items = []
    seen = set()
    for item in channel.findall("item"):
        title = clean(item.findtext("title"))
        link = clean(item.findtext("link"))
        source_node = item.find("source")
        source = clean(source_node.text if source_node is not None else "Google News")
        pub_raw = clean(item.findtext("pubDate"))
        if not title or not link or link in seen:
            continue
        seen.add(link)
        try:
            pub_date = parsedate_to_datetime(pub_raw).astimezone(timezone.utc).isoformat()
        except Exception:
            pub_date = ""
        items.append({
            "title": title,
            "url": link,
            "source": source,
            "publishedAt": pub_date,
            "publishedLabel": pub_raw
        })
        if len(items) >= 15:
            break
    if not items:
        raise RuntimeError("The RSS feed returned no usable headlines; keeping the previous digest")
    data = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "updatedDateIST": datetime.now(timezone.utc).astimezone(__import__("zoneinfo").ZoneInfo("Asia/Kolkata")).strftime("%d %b %Y, %I:%M %p IST"),
        "feed": FEED_URL,
        "items": items
    }
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {len(items)} headlines to {OUTPUT}")

if __name__ == "__main__":
    main()
