#!/usr/bin/env python3
import html, json, re, urllib.parse, urllib.request
from datetime import datetime, timezone, timedelta
from pathlib import Path
import xml.etree.ElementTree as ET

IST = timezone(timedelta(hours=5, minutes=30))
now = datetime.now(IST)
date_str = now.strftime("%Y-%m-%d")
month_str = now.strftime("%B %Y")

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

def rss_items(query):
    url = "https://news.google.com/rss/search?q=" + urllib.parse.quote(query) + "&hl=en-IN&gl=IN&ceid=IN:en"
    req = urllib.request.Request(url, headers={"User-Agent": "TASVIA-Current-Affairs/1.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        root = ET.fromstring(r.read())
    out=[]
    for item in root.findall("./channel/item"):
        title=clean(item.findtext("title"))
        desc=clean(item.findtext("description"))
        link=item.findtext("link") or ""
        pub=item.findtext("pubDate") or ""
        source=clean((item.find("source").text if item.find("source") is not None else "News source"))
        if title:
            out.append({"title":title,"description":desc,"link":link,"pubDate":pub,"source":source})
    return out

all_items=[]
for category, query in QUERIES:
    try:
        for x in rss_items(query):
            x["category"]=category
            if x["title"] not in [a["title"] for a in all_items]:
                all_items.append(x)
    except Exception as e:
        print(f"Feed failed: {category}: {e}")

# Prefer recent, useful stories and avoid duplicate/same-topic headlines.
selected=[]
seen=set()
for x in all_items:
    key=re.sub(r"[^a-z0-9]","",x["title"].lower())[:90]
    if key in seen: continue
    seen.add(key)
    selected.append(x)
    if len(selected)>=8: break

icons={"India":"🇮🇳","World":"🌐","Sports":"🏆","Science & Technology":"🔬","Economy":"💹"}
items=[]
for x in selected:
    summary=x["description"]
    # Google News descriptions can contain the article headline again; keep concise.
    if len(summary)>420: summary=summary[:417].rsplit(" ",1)[0]+"…"
    items.append({
        "category":x["category"],
        "icon":icons.get(x["category"],"📰"),
        "title":x["title"],
        "text":summary or x["title"],
        "source":f"{x['source']}, {date_str}",
        "url":x["link"]
    })

# If feeds temporarily fail, retain the previous content rather than publishing an empty page.
if not items:
    p=Path("current-affairs.json")
    if p.exists():
        print("No fresh feed items; retaining existing current-affairs.json")
        raise SystemExit(0)
    items=[{"category":"Current Affairs","icon":"📰","title":"Daily current affairs update","text":"Fresh current-affairs content will be available shortly.","source":"TASVIA Academy"}]

quiz=[]
for x in items[:5]:
    quiz.append({"q":f"Which topic is covered in today's {x['category']} current affairs?","a":x["title"]})

data={"date":date_str,"month":month_str,"title":"Daily Current Affairs","items":items,"quiz":quiz}
Path("current-affairs.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
archive=Path("current-affairs-history")
archive.mkdir(exist_ok=True)
(Path(archive)/f"{date_str}.json").write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print(f"Updated {date_str}: {len(items)} items")
