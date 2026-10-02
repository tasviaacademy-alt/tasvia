#!/usr/bin/env python3
import html, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET

IST = timezone(timedelta(hours=5, minutes=30))
now = datetime.now(IST)
date_str = now.strftime("%Y-%m-%d")
month_str = now.strftime("%B %Y")

HISTORY_DIR = Path("current-affairs-history")
HISTORY_DIR.mkdir(exist_ok=True)
TODAY_HISTORY = HISTORY_DIR / f"{date_str}.json"

if TODAY_HISTORY.exists():
    existing = json.loads(TODAY_HISTORY.read_text(encoding="utf-8"))
    Path("current-affairs.json").write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{date_str}: today's current-affairs edition already archived; no change.")
    raise SystemExit(0)

QUERIES = [
    ("India", "India current affairs India government national news"),
    ("World", "world international current affairs"),
    ("Sports", "India sports latest news"),
    ("Science & Technology", "India science technology latest news"),
    ("Economy", "India economy business latest news"),
]

def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()

def norm_title(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def rss_items(query):
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
    req = urllib.request.Request(url, headers={"User-Agent": "TASVIA-Current-Affairs/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    out = []
    for item in root.findall("./channel/item"):
        title = clean(item.findtext("title"))
        desc = clean(item.findtext("description"))
        link = item.findtext("link") or ""
        source = clean(item.find("source").text if item.find("source") is not None else "News source")
        if title:
            out.append({"title": title, "description": desc, "link": link, "source": source})
    return out

used_titles = set()
for archive in HISTORY_DIR.glob("*.json"):
    try:
        old = json.loads(archive.read_text(encoding="utf-8"))
        for item in old.get("items", []):
            used_titles.add(norm_title(item.get("title")))
    except Exception:
        continue

all_items = []
seen_today = set()
for category, query in QUERIES:
    try:
        for x in rss_items(query):
            x["category"] = category
            key = norm_title(x["title"])
            if key and key not in used_titles and key not in seen_today:
                seen_today.add(key)
                all_items.append(x)
    except Exception as e:
        print(f"Feed failed: {category}: {e}")

selected = all_items[:8]
icons = {"India":"🇮🇳", "World":"🌐", "Sports":"🏆", "Science & Technology":"🔬", "Economy":"💹"}
items = []
for x in selected:
    summary = x["description"]
    if len(summary) > 420:
        summary = summary[:417].rsplit(" ", 1)[0] + "…"
    items.append({
        "category": x["category"],
        "icon": icons.get(x["category"], "📰"),
        "title": x["title"],
        "text": summary or x["title"],
        "source": f"{x['source']}, {date_str}",
        "url": x["link"]
    })

if not items:
    p = Path("current-affairs.json")
    if p.exists():
        print("No unused fresh feed items; retaining previous content.")
        raise SystemExit(0)
    raise RuntimeError("No fresh current-affairs items available; refusing to publish empty content.")

quiz = [{"q": f"Which topic is covered in today's {x['category']} current affairs?", "a": x["title"]} for x in items[:5]]
data = {"date": date_str, "month": month_str, "title": "Daily Current Affairs", "items": items, "quiz": quiz}

text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
Path("current-affairs.json").write_text(text, encoding="utf-8")
TODAY_HISTORY.write_text(text, encoding="utf-8")
print(f"Updated {date_str}: {len(items)} fresh, previously unused current-affairs stories")
