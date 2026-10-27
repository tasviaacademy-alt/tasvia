#!/usr/bin/env python3
import email.utils
import html, json, re, urllib.parse, urllib.request
from html.parser import HTMLParser
from datetime import datetime, timezone, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET

IST = timezone(timedelta(hours=5, minutes=30))
now = datetime.now(IST)
date_str = now.strftime("%Y-%m-%d")
month_str = now.strftime("%B %Y")
two_days_ago = (now - timedelta(days=2)).strftime("%Y-%m-%d")

HISTORY_DIR = Path("current-affairs-history")
HISTORY_DIR.mkdir(exist_ok=True)
TODAY_HISTORY = HISTORY_DIR / f"{date_str}.json"

QUERIES = [
    ("India", f"India current affairs India government national news after:{two_days_ago}"),
    ("World", f"world international current affairs after:{yesterday}"),
    ("Sports", f"India sports latest news after:{yesterday}"),
    ("Science & Technology", f"India science technology latest news after:{yesterday}"),
    ("Economy", f"India economy business latest news after:{yesterday}"),
]

def clean(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()

class ArticleSummaryParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta = []
        self.paragraphs = []
        self._in_p = False
        self._p = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag.lower() == "meta":
            key = (attrs.get("property") or attrs.get("name") or "").casefold()
            if key in {"description", "og:description", "twitter:description"}:
                value = attrs.get("content", "")
                if value:
                    self.meta.append(value)
        elif tag.lower() == "p":
            self._in_p = True
            self._p = []

    def handle_data(self, data):
        if self._in_p:
            self._p.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "p" and self._in_p:
            paragraph = clean(" ".join(self._p))
            if len(paragraph) >= 70:
                self.paragraphs.append(paragraph)
            self._in_p = False
            self._p = []


def fetch_article_summary(link, title):
    """Try the linked publisher page when Google News RSS only supplies a headline."""
    if not str(link).startswith(("https://", "http://")):
        return ""
    request = urllib.request.Request(
        link,
        headers={"User-Agent": "Mozilla/5.0 (compatible; TASVIA-Current-Affairs/2.1)"}
    )
    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            content_type = response.headers.get("Content-Type", "")
            if "html" not in content_type.casefold():
                return ""
            raw = response.read(1_200_000)
            charset = response.headers.get_content_charset() or "utf-8"
        parser = ArticleSummaryParser()
        parser.feed(raw.decode(charset, errors="replace"))
    except Exception as exc:
        print(f"Article summary fetch failed for {title[:70]}: {type(exc).__name__}")
        return ""

    for candidate in parser.meta + parser.paragraphs:
        candidate = clean(candidate)
        if quality_story({"title": title, "description": candidate}):
            return candidate[:1200]
    return ""


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
    if re.search(r"\b(home|current affairs|latest news|live updates|live blog|live stream|fixtures|betting|odds|predictions?|opinion|news feed|watch live)\b", title_lower):
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

    # Current, source-backed templates for recurring school-relevant topics.
    if "estic 2026" in low and re.search(r"\b12\s+(?:thematic\s+)?areas\b", low):
        return {"q": "How many thematic areas are planned for discussion at ESTIC 2026?", "a": "12 thematic areas"}
    if "cbse" in low and "school-to-work transition" in low:
        return {"q": "What is the main focus of the CBSE National Summit held on 26–27 October?", "a": "Facilitating School-to-Work Transition"}
    if "relief" in low and (re.search(r"\b31\s+march\s+2027\b", low) or re.search(r"\bmarch\s+31,?\s+2027\b", low)):
        return {"q": "Until what date has the RELIEF support scheme been extended?", "a": "31 March 2027"}
    if "jharkhand" in low and "bcci" in low and "scorer" in low:
        return {"q": "Which cricket board was asked to review the disputed under-19 women's match result?", "a": "Board of Control for Cricket in India (BCCI)"}
    if "third t20i" in low and "new zealand" in low and re.search(r"\b2\s*[-–]\s*0\b", low):
        return {"q": "What was India's series lead before the third T20I against New Zealand?", "a": "2–0"}
    if "tilak varma" in low and re.search(r"\b51\s+off\s+(?:just\s+)?26\s+balls?\b", low):
        return {"q": "How many runs did Tilak Varma score in the second T20I?", "a": "51 runs off 26 balls"}
    if "reserve bank of india" in low and "data centre" in low and "bhubaneswar" in low:
        return {"q": "Which city will host the RBI Data Centre and Cybersecurity Training Institute?", "a": "Bhubaneswar"}
    if "semiconductor summit" in low and "madhya pradesh" in low and re.search(r"5,800\s+crore", low):
        return {"q": "Which state reported semiconductor and technology proposals worth over ₹5,800 crore?", "a": "Madhya Pradesh"}
    if "india-germany" in low and re.search(r"six (?:industrial )?technology areas", low):
        return {"q": "How many technology areas were discussed in the India–Germany talks?", "a": "Six"}
    if ("india meteorological department" in low or re.search(r"\bIMD\b", combined)) and re.search(r"rain|rainfall|downpour", low):
        return {"q": "Which agency issued the heavy-rain alerts mentioned in the report?", "a": "India Meteorological Department (IMD)"}

    if "cyclone arnab" in low and "bapatla" in low and "visakhapatnam" in low:
        return {"q": "Near which Andhra Pradesh coastal stretch could Cyclone Arnab approach on 28 October, according to the forecast?", "a": "Between Bapatla and Visakhapatnam"}
    if "devdutt padikkal" in low and re.search(r"\b199\b", combined):
        return {"q": "What score did Devdutt Padikkal make against New Zealand A?", "a": "199 runs"}
    if "india women" in low and "zimbabwe" in low and re.search(r"\b121[- ]runs?\b", low):
        return {"q": "By how many runs did India Women defeat Zimbabwe in the second ODI?", "a": "121 runs"}
    if "jogen chowdhury" in low and re.search(r"\b87\b", combined):
        return {"q": "How old was painter Jogen Chowdhury when he died?", "a": "87 years"}
    if "operation trident" in low and re.search(r"\b18 arrests\b", low):
        return {"q": "How many arrests were reported during Operation Trident?", "a": "18 people"}

    # Extract other concrete facts when a source gives a clear number or location.
    score = re.search(r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2}).{0,70}\b(\d{1,3})\s+off\s+(?:just\s+)?(\d{1,3})\s+balls?\b", combined)
    if score:
        return {"q": f"What score did {score.group(1)} make in the reported match?", "a": f"{score.group(2)} runs off {score.group(3)} balls"}
    amount = re.search(r"\b(?:cross(?:ed|es)?|exceed(?:ed|s)?|over|more than|above|reached|rose to|increased to)\s+(?:₹|Rs\.?\s*)?([\d,]+(?:\.\d+)?)\s*(crore|lakh crore|billion|million|jobs|athletes|participants)\b", combined, re.I)
    if amount:
        unit = amount.group(2).lower()
        return {"q": "What amount or figure did the report state?", "a": f"{amount.group(1)} {unit}"}

    if "urban mobility india" in low and "bhubaneswar" in low:
        return {"q": "What theme did the 19th Urban Mobility India Conference focus on?", "a": "Urban Accessibility and Liveability in Digital Age"}
    if "pmi" in low and re.search(r"\b56\.7\b", combined):
        return {"q": "What was the HSBC Flash India Composite PMI reading reported for October?", "a": "56.7"}
    if "atmanirbhar bharat" in low and "chamba" in low:
        return {"q": "Where did the Atmanirbhar Bharat – Destination Himachal Expo 2026 open?", "a": "Chaugan Ground in Chamba"}
    if "chancellors conclave" in low and "goa" in low:
        return {"q": "In which state was Chancellors Conclave 2026 held?", "a": "Goa"}
    if "new zealand" in low and "india" in low and ("t20" in low or "cricket" in low) and re.search(r"four[- ]wicket", low):
        return {"q": "By how many wickets did India beat New Zealand in the first T20I?", "a": "Four wickets"}

    # Limited factual fallbacks: only create a quiz when the feed gives a concrete
    # value or event location; never turn the headline itself into the answer.
    value = re.search(r"\b(?:rose|increased|climbed|reached|hit)\s+(?:to\s+)?(\d+(?:\.\d+)?%?)", combined, re.I)
    if value and re.search(r"\b(?:PMI|percent|per cent|growth|inflation|score|outlay|crore|kilometres|km)\b", low):
        return {"q": "What figure did the report give for the latest measured result?", "a": value.group(1)}
    location = re.search(r"\b(?:inaugurated|opened|began|hosted|held|launched)\b.{0,100}\b(?:in|at)\s+(Bhubaneswar|Chamba|Goa|Christchurch|New Delhi|Delhi|Mumbai|Kolkata|Hyderabad|Nizamabad|Amaravati|Chennai|Bengaluru|India)\b", combined, re.I)
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
        Path("current-affairs.json").write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
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
        # Allow up to 48 hours so a delayed feed does not leave the edition stale.
        age = now - published
        if age < timedelta(hours=-1) or age > timedelta(hours=48):
            continue
        candidate = {
            "title": title,
            "description": desc,
            "link": link,
            "source": source,
            "published": published
        }
        if not quality_story(candidate):
            enriched = fetch_article_summary(link, title)
            if enriched:
                candidate["description"] = enriched
        if not quality_story(candidate):
            continue
        out.append(candidate)
    return out

used_titles = set()
# Avoid repeating recent stories, but do not permanently exhaust the news feed.
# A 14-day rolling window preserves freshness while allowing genuinely updated topics later.
for archive in HISTORY_DIR.glob("*.json"):
    # Do not treat today's invalid archive as a prior story when regenerating it.
    if archive.stem == date_str:
        continue
    try:
        archive_date = datetime.strptime(archive.stem, "%Y-%m-%d").date()
        if (now.date() - archive_date).days > 14:
            continue
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

# Select only stories that can support a factual quiz question. This avoids
# publishing a story set whose quiz is forced to fall back to headline-identification.
all_items.sort(key=lambda x: x["published"], reverse=True)
quiz_candidates = []
for candidate in all_items:
    question = build_quiz(candidate)
    if question is not None:
        quiz_candidates.append((candidate, question))

selected = []
category_counts = {}
selected_titles = set()
for candidate, question in quiz_candidates:
    category = candidate["category"]
    if category_counts.get(category, 0) >= 2:
        continue
    selected.append((candidate, question))
    selected_titles.add(norm_title(candidate["title"]))
    category_counts[category] = category_counts.get(category, 0) + 1
    if len(selected) == 5:
        break

# If the feed is unusually concentrated in one category, fill from remaining
# factual stories rather than failing solely because of the diversity cap.
if len(selected) < 5:
    for candidate, question in quiz_candidates:
        key = norm_title(candidate["title"])
        if key in selected_titles:
            continue
        selected.append((candidate, question))
        selected_titles.add(key)
        if len(selected) == 5:
            break

if len(selected) < 5:
    raise RuntimeError(
        f"Only {len(selected)} recent stories produced factual quiz questions; "
        "refusing to publish generic headlines or headline-only summaries."
    )

icons = {"India":"🇮🇳", "World":"🌐", "Sports":"🏆", "Science & Technology":"🔬", "Economy":"💹"}
items = []
quiz = []
for candidate, question in selected:
    summary = candidate["description"]
    if len(summary) > 420:
        summary = summary[:417].rsplit(" ", 1)[0] + "…"
    items.append({
        "category": candidate["category"],
        "icon": icons.get(candidate["category"], "📰"),
        "title": candidate["title"],
        "text": summary,
        "source": f"{candidate['source']}, {candidate['published'].strftime('%Y-%m-%d')}",
        "url": candidate["link"]
    })
    quiz.append(question)

data = {"date": date_str, "month": month_str, "title": "Daily Current Affairs", "items": items, "quiz": quiz}

text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
Path("current-affairs.json").write_text(text, encoding="utf-8")
TODAY_HISTORY.write_text(text, encoding="utf-8")
print(f"Updated {date_str}: {len(items)} genuinely recent, previously unused current-affairs stories")
