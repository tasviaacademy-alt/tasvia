#!/usr/bin/env python3
"""Fetch a fresh, Nizamabad-focused daily news digest from Google News RSS."""
import json
import re
import time
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import quote
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "local-news.json"
QUERIES = [
    '"Nizamabad" Telangana news',
    '"Nizamabad district" news',
    '"Bodhan" OR "Armoor" OR "Banswada" Telangana news',
    '"Dichpally" OR "Nandipet" OR "Balkonda" news',
    '"Kamareddy" district news',
]
LOCAL_TERMS = (
    "nizamabad", "bodhan", "armoor", "banswada", "bansvada",
    "dichpally", "dichpalli", "nandipet", "balkonda", "navipet",
    "indalwai", "kotagiri", "varni", "yellareddy", "kamareddy",
)
IST = ZoneInfo("Asia/Kolkata")


def clean(value):
    return re.sub(r"\s+", " ", (value or "")).strip()


def fetch(url, attempts=4):
    last_error = None
    for attempt in range(attempts):
        request = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (compatible; TASVIA-Academy-Local-News/2.0)"}
        )
        try:
            with urllib.request.urlopen(request, timeout=25) as response:
                return response.read()
        except (HTTPError, URLError, TimeoutError) as exc:
            last_error = exc
            code = getattr(exc, "code", None)
            if code not in (None, 429, 500, 502, 503, 504) and not isinstance(exc, (URLError, TimeoutError)):
                raise
            if attempt + 1 < attempts:
                time.sleep(min(2 ** attempt, 8))
    raise RuntimeError(f"RSS request failed after {attempts} attempts: {last_error}")


def is_local(title, description):
    text = clean(f"{title} {description}").casefold()
    return any(term in text for term in LOCAL_TERMS)


def main():
    now = datetime.now(timezone.utc)
    oldest_allowed = now - timedelta(hours=72)
    candidates = {}
    failures = []

    for query in QUERIES:
        feed_url = (
            "https://news.google.com/rss/search?q=" + quote(query + " when:3d")
            + "&hl=en-IN&gl=IN&ceid=IN:en"
        )
        try:
            root = ET.fromstring(fetch(feed_url))
            channel = root.find("channel")
            if channel is None:
                raise RuntimeError("RSS feed did not contain a channel")
            for item in channel.findall("item"):
                title = clean(item.findtext("title"))
                link = clean(item.findtext("link"))
                description = clean(item.findtext("description"))
                source_node = item.find("source")
                source = clean(source_node.text if source_node is not None else "Google News")
                pub_raw = clean(item.findtext("pubDate"))
                if not title or not link or not is_local(title, description):
                    continue
                try:
                    parsed = parsedate_to_datetime(pub_raw)
                    if parsed.tzinfo is None:
                        parsed = parsed.replace(tzinfo=timezone.utc)
                    published = parsed.astimezone(timezone.utc)
                except Exception:
                    continue
                if published < oldest_allowed or published > now + timedelta(hours=1):
                    continue
                key = re.sub(r"[^a-z0-9]+", " ", title.casefold()).strip()
                candidates[key] = {
                    "title": title,
                    "url": link,
                    "source": source,
                    "publishedAt": published.isoformat(),
                    "publishedLabel": published.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST"),
                }
        except Exception as exc:
            failures.append(f"{query}: {type(exc).__name__}: {exc}")
            print(f"Feed failed for {query!r}: {type(exc).__name__}")

    items = sorted(candidates.values(), key=lambda row: row["publishedAt"], reverse=True)[:15]
    if not items:
        for failure in failures:
            print(failure)
        print("No verified local headlines from the last 72 hours; keeping the previous digest unchanged.")
        return

    data = {
        "updatedAt": now.isoformat(),
        "updatedDateIST": now.astimezone(IST).strftime("%d %b %Y, %I:%M %p IST"),
        "feed": "Google News RSS; multiple Nizamabad and nearby-town queries",
        "items": items,
    }
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
    print(f"Wrote {len(items)} fresh local headlines to {OUTPUT}")
    if failures:
        print(f"Warning: {len(failures)} of {len(QUERIES)} query feeds failed; successful feeds were retained.")


if __name__ == "__main__":
    main()
