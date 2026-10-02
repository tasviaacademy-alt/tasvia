#!/usr/bin/env python3
import json
import random
from datetime import datetime, timezone, timedelta
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
now = datetime.now(IST)
date_str = now.strftime("%Y-%m-%d")

BANK_PATH = Path("gk-question-bank.json")
DAILY_PATH = Path("daily-gk.json")
HISTORY_DIR = Path("daily-gk-history")
HISTORY_DIR.mkdir(exist_ok=True)
TODAY_HISTORY = HISTORY_DIR / f"{date_str}.json"

bank = json.loads(BANK_PATH.read_text(encoding="utf-8"))["questions"]

# If today's set already exists, never regenerate it differently.
if TODAY_HISTORY.exists():
    existing = json.loads(TODAY_HISTORY.read_text(encoding="utf-8"))
    if len(existing.get("questions", [])) == 5:
        DAILY_PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{date_str}: today's 5 GK questions already archived; no change.")
        raise SystemExit(0)

# Collect every question ID used on previous days.
used_ids = set()
for archive in HISTORY_DIR.glob("*.json"):
    try:
        data = json.loads(archive.read_text(encoding="utf-8"))
        for item in data.get("questions", []):
            if item.get("id"):
                used_ids.add(item["id"])
    except Exception:
        continue

unused = [q for q in bank if q.get("id") not in used_ids]
if len(unused) < 5:
    raise RuntimeError(
        f"GK question bank exhausted: only {len(unused)} unused questions remain; "
        "refusing to repeat any question."
    )

# Deterministic daily shuffle, so a rerun before archiving gives the same set.
rng = random.Random(date_str)
rng.shuffle(unused)

# Prefer a balanced daily set: maximum two questions from one category.
selected = []
category_counts = {}
for item in unused:
    cat = item.get("category", "general")
    if category_counts.get(cat, 0) >= 2:
        continue
    selected.append({"id": item["id"], "q": item["q"], "a": item["a"]})
    category_counts[cat] = category_counts.get(cat, 0) + 1
    if len(selected) == 5:
        break

# If category balancing prevented five, fill from remaining unused questions.
if len(selected) < 5:
    selected_ids = {x["id"] for x in selected}
    for item in unused:
        if item["id"] in selected_ids:
            continue
        selected.append({"id": item["id"], "q": item["q"], "a": item["a"]})
        if len(selected) == 5:
            break

if len({x["id"] for x in selected}) != 5:
    raise RuntimeError("Duplicate question IDs detected in today's set.")

data = {
    "date": date_str,
    "title": "Daily General Knowledge",
    "questions": selected
}

text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
DAILY_PATH.write_text(text, encoding="utf-8")
TODAY_HISTORY.write_text(text, encoding="utf-8")

print(
    f"Updated {date_str}: 5 non-repeating GK questions. "
    f"{len(unused) - 5} unused questions remain."
)
