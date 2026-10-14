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
    bank.extend(json.loads(EXTRA_BANK_PATH.read_text(encoding="utf-8")).get("questions", []))

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

# This portal displays direct answers, not multiple-choice options. Exclude quiz-bank entries\n# whose answer only makes sense when unseen options are available.\nunused = [\n    q for q in bank\n    if q.get("id") not in used_ids\n    and str(q.get("a", "")).strip().casefold() not in {"all of these", "all of the above", "both a and b", "both a and c", "none of these", "none of the above"}\n]
if len(unused) < 5:
    raise RuntimeError(
        f"GK question bank exhausted: only {len(unused)} unused questions remain; "
        "refusing to repeat any question."
    )

# Deterministic daily shuffle, so a rerun before archiving gives the same set.
rng = random.Random(date_str)
rng.shuffle(unused)

# Choose one question per category in rounds before allowing any category to repeat.
# This prevents large geography/animal categories from dominating the daily set.
by_category = {}
for item in unused:
    by_category.setdefault(item.get("category", "general"), []).append(item)

categories = list(by_category)
rng.shuffle(categories)
for items in by_category.values():
    rng.shuffle(items)

selected = []
for round_index in range(max((len(items) for items in by_category.values()), default=0)):
    for category in categories:
        items = by_category[category]
        if round_index < len(items) and len(selected) < 5:
            item = items[round_index]
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
