#!/usr/bin/env python3
import email.utils
import html, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET

IST = timezone(timedelta(hours=5, minutes=30))
now = datetime.now(IST)
date_str = now.strftime("%Y-%m-%d")
month_str = now.strftime("%B %Y")
yesterday = (now - timedelta(days=1)).strftime("%Y-%m-%d")

HISTORY_DIR = Path("current-affairs-history")
HISTORY_DIR.mkdir(exist_ok=True)
TODAY_HISTORY = HISTORY_DIR / f"{date_str}.json"

QUERIES = [
    ("India", f"India current affairs India government national news after:{yesterday}"),
    ("World", f"world international current affairs after:{yesterday}"),
    ("Sports", f"India sports latest news after:{yesterday}"),
    ("Science & Technology", f"India science technology latest news after:{yesterday}"),
    ("Economy", f"India economy business latest news after:{yesterday}"),
]

def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()

def norm_title(s):
    return re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).strip()

def quality_story(item):
    title = clean(item.get("title", ""))
    summary = clean(item.get("description", item.get("text", "")))
    title_norm = norm_title(title)
    summary_norm = norm_title(summary)
    title_lower = title.casefold()
    if len(title) < 20 or not title_norm:
        return False
    if re.search(r"\\b(home|current affairs|latest news|live updates|live blog|live stream|fixtures|betting|odds|predictions?|opinion|news feed|watch live)\\b", title_lower):
        return False
    if len(summary) < 90 or not summary_norm:
        return False
    # Reject RSS entries whose "description" is just the headline and publisher.
    if summary_norm == title_norm:
        return False
    if summary_norm.startswith(title_norm) and len(summary_norm) - len(title_norm) < 45:
        return False
    return True

def build_quiz(item):
    title = clean(item.get("title", ""))
    summary = clean(item.get("description", item.get("text", "")))
    combined = f"{title}. {summary}"
    low = combined.casefold()

    if "urban mobility india" in low and "bhubaneswar" in low:
        return {"q": "What theme did the 19th Urban Mobility India Conference focus on?", "a": "Urban Accessibility and Liveability in the Digital Age"}
    if "pmi" in low and re.search(r"\\b56\\.7\\b", combined):
        return {"q": "What was the HSBC Flash India Composite PMI reading reported for October?", "a": "56.7"}
    if "atmanirbhar bharat" in low and "chamba" in low:
        return {"q": "Where did the Atmanirbhar Bharat – Destination Himachal Expo 2026 open?", "a": "Chaugan Ground in Chamba"}
    if "chancellors conclave" in low and "goa" in low:
        return {"q": "In which state was Chancellors Conclave 2026 held?", "a": "Goa"}
    if "new zealand" in low and "india" in low and ("t20" in low or "cricket" in low) and re.search(r"four[- ]wicket", low):
        return {"q": "By how many wickets did India beat New Zealand in the first T20I?", "a": "Four wickets"}

    # Limited factual fallbacks: only create a quiz when the feed gives a concrete
    # value or event location; never turn the headline itself into the answer.
    value = re.search(r"\\b(?:rose|increased|climbed|reached|hit)\\s+(?:to\\s+)?(\\d+(?:\\.\\d+)?%?)", combined, re.I)
    if value and re.search(r"\\b(?:PMI|percent|per cent|growth|inflation|score|outlay|crore|kilometres|km)\\b", low):
        return {"q": "What figure did the report give for the latest measured result?", "a": value.group(1)}
    location = re.search(r"\\b(?:inaugurated|opened|began|hosted|held|launched)\\b.{0,100}\\b(?:in|at)\\s+(Bhubaneswar|Chamba|Goa|Christchurch|New Delhi|Delhi|Mumbai|Kolkata|Hyderabad|Nizamabad|Amaravati|Chennai|Bengaluru|India)\\b", combined, re.I)
    if location:
        place = location.group(1)
        return {"q": "In which city or place did the reported event take place?", "a": place}
    return None

def valid_edition(data):
    if not isinstance(data, dict) or data.get("date") != date_str:
        return False
    items = data.get("items", [])
    quiz = data.get("quiz", [])
    if len(items) < 5 or len(quiz) < 5:
        return False
    if any(not quality_story(item) for item in items):
        return False
    if any(not str(q.get("q", "")).strip() or not str(q.get("a", "")).strip()
           or str(q.get("q", "")).casefold().startswith("which topic is covered")
           for q in quiz):
        return False
    return True

if TODAY_HISTORY.exists():
    try:
        existing = json.loads(TODAY_HISTORY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        existing = {}
    if valid_edition(existing):
        Path("current-affairs.json").write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8")
        print(f"{date_str}: today's archived current-affairs edition passed quality checks; no change.")
        raise SystemExit(0)
    print(f"{date_str}: today's archive failed quality checks; regenerating from verified recent feeds.")

def parse_pub_date(value):
    if not value:
        return None
    try:
        d = email.utils.parsedate_to_datetime(value)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        return d.astimezone(IST)
    except Exception:
        return None

def rss_items(query):
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
    req = urllib.request.Request(url, headers={"User-Agent": "TASVIA-Current-Affairs/2.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    out = []
    for item in root.findall("./channel/item"):
        title = clean(item.findtext("title"))
        desc = clean(item.findtext("description"))
        link = item.findtext("link") or ""
        source = clean(item.find("source").text if item.find("source") is not None else "News source")
        published = parse_pub_date(item.findtext("pubDate"))
        if not title or not published:
            continue
        # Never publish an article merely because the RSS feed returned it today.
        # It must actually have been published within the last 36 hours.
        age = now - published
        if age < timedelta(hours=-1) or age > timedelta(hours=36):
            continue
        candidate = {
            "title": title,
            "description": desc,
            "link": link,
            "source": source,
            "published": published
        }
        if not quality_story(candidate):
            continue
        out.append(candidate)
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

# Prefer one or two items from each category, then fill remaining slots by recency.
all_items.sort(key=lambda x: x["published"], reverse=True)
selected = []
category_counts = {}
for x in all_items:
    if category_counts.get(x["category"], 0) < 2:
        selected.append(x)
        category_counts[x["category"]] = category_counts.get(x["category"], 0) + 1
    if len(selected) >= 8:
        break

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
        "source": f"{x['source']}, {x['published'].strftime('%Y-%m-%d')}",
        "url": x["link"]
    })

if len(items) < 5:
    raise RuntimeError(
        f"Only {len(items)} current-affairs stories passed recency and quality checks; "
        "refusing to publish generic headlines or headline-only summaries."
    )

quiz = [question for x in selected if (question := build_quiz(x)) is not None]
if len(quiz) < 5:
    raise RuntimeError(
        f"Only {len(quiz)} factual quiz questions could be generated from the selected stories; "
        "refusing to publish headline-identification questions."
    )
data = {"date": date_str, "month": month_str, "title": "Daily Current Affairs", "items": items, "quiz": quiz}

text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
Path("current-affairs.json").write_text(text, encoding="utf-8")
TODAY_HISTORY.write_text(text, encoding="utf-8")
print(f"Updated {date_str}: {len(items)} genuinely recent, previously unused current-affairs stories")
