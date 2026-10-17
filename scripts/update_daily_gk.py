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

def answer_key(value):
    return " ".join(str(value or "").casefold().strip().split())

def valid_daily(data):
    if not isinstance(data, dict) or data.get("schemaVersion") != 3:
        return False
    questions = data.get("questions", [])
    if len(questions) != 5:
        return False
    ids = [q.get("id") for q in questions]
    if any(not qid for qid in ids) or len(set(ids)) != 5:
        return False
    for q in questions:
        options = q.get("options")
        if not isinstance(options, list) or len(options) != 4:
            return False
        if len({answer_key(x) for x in options}) != 4:
            return False
        if answer_key(q.get("a")) not in {answer_key(x) for x in options}:
            return False
    return True

# Keep today's set stable only after it passes the current MCQ schema.
if TODAY_HISTORY.exists():
    try:
        existing = json.loads(TODAY_HISTORY.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        existing = {}
    if valid_daily(existing):
        DAILY_PATH.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{date_str}: today's five MCQs are already archived; no change.")
        raise SystemExit(0)

# An invalid legacy archive for today must not block regeneration. All older
# archive IDs remain excluded, while today's invalid IDs can be replaced.
used_ids = set()
for archive in HISTORY_DIR.glob("*.json"):
    if archive == TODAY_HISTORY:
        continue
    try:
        data = json.loads(archive.read_text(encoding="utf-8"))
        for item in data.get("questions", []):
            if item.get("id"):
                used_ids.add(item["id"])
    except (OSError, json.JSONDecodeError):
        continue

option_dependent_answers = {
    "all of these", "all of the above", "both a and b", "both a and c",
    "none of these", "none of the above",
}
def option_group(category):
    c = str(category or "").casefold()
    if c in {"geography", "world geography", "indian geography"}:
        return "geography"
    if c == "animals":
        return "animals"
    if c in {"brain-teasers", "brain teasers"}:
        return "logic"
    if c in {"indian history", "indian culture", "literature & culture"}:
        return "history-culture"
    if c in {"indian general knowledge", "indian polity", "national symbols", "economics"}:
        return "india"
    if c in {"science", "science & space", "human biology", "astronomy", "environment", "computer basics", "mathematics"}:
        return "science-tech"
    if c == "sports":
        return "sports"
    return c

CUSTOM_DISTRACTORS = {
    "static-sports-olympics": ["Every two years", "Every three years", "Every five years"],
    "static-sports-chess": ["32", "48", "100"],
    "otq-brain-teasers-2310": ["1", "2", "3"],
}

def eligible(q):
    question = str(q.get("q", "")).strip()
    answer = str(q.get("a", "")).strip()
    key = answer_key(answer)
    return bool(
        q.get("id") and question and answer
        and len(question) <= 320 and len(answer) <= 120
        and key not in option_dependent_answers
        and key not in {"true", "false", "yes", "no"}
    )

unused = [q for q in bank if eligible(q) and q["id"] not in used_ids]
if len(unused) < 5:
    raise RuntimeError(
        f"GK question bank exhausted: only {len(unused)} unused eligible questions remain; "
        "refusing to repeat any question."
    )

# Deterministic daily selection and option ordering.
rng = random.Random(date_str)
rng.shuffle(unused)
by_category = {}
for item in unused:
    by_category.setdefault(item.get("category", "General Knowledge"), []).append(item)

categories = list(by_category)
rng.shuffle(categories)
for items in by_category.values():
    rng.shuffle(items)

selected_raw = []
max_rounds = max((len(items) for items in by_category.values()), default=0)
for round_index in range(max_rounds):
    for category in categories:
        items = by_category[category]
        if round_index < len(items) and len(selected_raw) < 5:
            selected_raw.append(items[round_index])
    if len(selected_raw) == 5:
        break

if len(selected_raw) != 5 or len({q["id"] for q in selected_raw}) != 5:
    raise RuntimeError("Could not select five unique GK questions.")

# Build four-option MCQs. Prefer distractors from the same category; use the
# wider bank only when that category does not contain three distinct alternatives.
answer_pools = {}
all_answers = {}
for q in bank:
    if not eligible(q):
        continue
    key = answer_key(q["a"])
    if key:
        value = str(q["a"]).strip()
        all_answers.setdefault(key, value)
        group = option_group(q.get("category"))
        answer_pools.setdefault(group, {})
        answer_pools[group].setdefault(key, value)

questions = []
for q in selected_raw:
    correct = str(q["a"]).strip()
    correct_key = answer_key(correct)
    curated = CUSTOM_DISTRACTORS.get(q["id"])
    provided = q.get("options")
    if isinstance(provided, list) and len(provided) == 4 and correct_key in {answer_key(x) for x in provided}:
        options = list(provided)
    elif curated and len({answer_key(x) for x in curated + [correct]}) == 4:
        options = [correct] + curated
        rng.shuffle(options)
    else:
        pool = answer_pools.get(option_group(q.get("category")), {})
        distractor_pool = [value for key, value in pool.items() if key != correct_key]
        if len(distractor_pool) < 3:
            distractor_pool = [value for key, value in all_answers.items() if key != correct_key]
        if len(distractor_pool) < 3:
            raise RuntimeError(f"Not enough distinct answer options for question {q['id']}.")
        rng.shuffle(distractor_pool)
        options = [correct] + distractor_pool[:3]
        rng.shuffle(options)
    questions.append({
        "id": q["id"],
        "category": q.get("category", "General Knowledge"),
        "q": str(q["q"]).strip(),
        "a": correct,
        "options": options,
    })

data = {"schemaVersion": 3, "date": date_str, "title": "Daily General Knowledge", "questions": questions}
text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
DAILY_PATH.write_text(text, encoding="utf-8")
TODAY_HISTORY.write_text(text, encoding="utf-8")
print(f"Updated {date_str}: 5 unique MCQs with A-D options; {len(unused) - 5} unused questions remain.")
