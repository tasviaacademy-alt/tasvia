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
EXTRA_BANK_PATH = Path("static-gk-extra.json")
if EXTRA_BANK_PATH.exists():
    bank.extend(
        json.loads(EXTRA_BANK_PATH.read_text(encoding="utf-8")).get("questions", [])
    )

# Keep today's set stable if the workflow is run more than once.
if TODAY_HISTORY.exists():
    existing = json.loads(TODAY_HISTORY.read_text(encoding="utf-8"))
    if len(existing.get("questions", [])) == 5:
        DAILY_PATH.write_text(
            json.dumps(existing, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"{date_str}: today's 5 GK questions already archived; no change.")
        raise SystemExit(0)

# Collect all question IDs already used in previous daily sets.
used_ids = set()
for archive in HISTORY_DIR.glob("*.json"):
    try:
        data = json.loads(archive.read_text(encoding="utf-8"))
        for item in data.get("questions", []):
            if item.get("id"):
                used_ids.add(item["id"])
    except (OSError, json.JSONDecodeError):
        continue

# Answers are displayed directly in the portal, so exclude answers that depend
# on unseen multiple-choice options.
option_dependent_answers = {
    "all of these",
    "all of the above",
    "both a and b",
    "both a and c",
    "none of these",
    "none of the above",
}
unused = [
    q for q in bank
    if q.get("id")
    and q.get("id") not in used_ids
    and str(q.get("a", "")).strip().casefold() not in option_dependent_answers
    and str(q.get("q", "")).strip()
    and str(q.get("a", "")).strip()
]

if len(unused) < 5:
    raise RuntimeError(
        f"GK question bank exhausted: only {len(unused)} unused questions remain; "
        "refusing to repeat any question."
    )

# Deterministic daily shuffle: reruns produce the same selection for this date.
rng = random.Random(date_str)
rng.shuffle(unused)

# Spread questions across categories before selecting a second from any category.
by_category = {}
for item in unused:
    by_category.setdefault(item.get("category", "General Knowledge"), []).append(item)

categories = list(by_category)
rng.shuffle(categories)
for items in by_category.values():
    rng.shuffle(items)

selected = []
max_rounds = max((len(items) for items in by_category.values()), default=0)
for round_index in range(max_rounds):
    for category in categories:
        items = by_category[category]
        if round_index < len(items) and len(selected) < 5:
            item = items[round_index]
            selected.append({
                "id": item["id"],
                "category": item.get("category", "General Knowledge"),
                "q": item["q"],
                "a": item["a"],
            })
    if len(selected) == 5:
        break

if len(selected) != 5 or len({item["id"] for item in selected}) != 5:
    raise RuntimeError("Could not select five unique GK questions.")

data = {
    "date": date_str,
    "title": "Daily General Knowledge",
    "questions": selected,
}
text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
DAILY_PATH.write_text(text, encoding="utf-8")
TODAY_HISTORY.write_text(text, encoding="utf-8")

print(f"Updated {date_str}: 5 non-repeating GK questions; {len(unused) - 5} unused questions remain.")
