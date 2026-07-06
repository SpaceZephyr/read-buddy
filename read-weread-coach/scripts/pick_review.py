#!/usr/bin/env python3
"""Pick a non-duplicate highlight from the WeRead corpus for daily review.

Usage:
  python3 pick_review.py             # print JSON to stdout
  python3 pick_review.py --notify    # also send macOS notification
"""
import json
import os
import random
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

CORPUS = Path("/tmp/read-weread-coach/corpus.json")
HISTORY = Path.home() / ".claude/skills/read-weread-coach/state/review_history.jsonl"


def load_corpus():
    if not CORPUS.exists():
        print("Corpus not found. Run fetch_corpus.py first.", file=sys.stderr)
        sys.exit(1)
    return json.loads(CORPUS.read_text(encoding="utf-8"))


def load_history():
    if not HISTORY.exists():
        return set()
    seen = set()
    for line in HISTORY.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            seen.add(json.loads(line)["bookmarkId"])
        except Exception:
            continue
    return seen


def reset_history():
    """Archive and reset history when all marks have been shown."""
    if HISTORY.exists():
        archive = HISTORY.with_suffix(f".{int(time.time())}.bak.jsonl")
        HISTORY.rename(archive)
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    HISTORY.touch()


def append_history(bm_id):
    HISTORY.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY.open("a", encoding="utf-8") as f:
        f.write(json.dumps({
            "bookmarkId": bm_id,
            "shown_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }, ensure_ascii=False) + "\n")


def pick(marks, seen):
    candidates = [m for m in marks if m.get("bookmarkId") and m["bookmarkId"] not in seen]
    if not candidates:
        return None
    # Weight: older highlights get higher weight (1 + days_old/365)
    now = time.time()
    weights = []
    for m in candidates:
        ts = m.get("createTime", now)
        days_old = max(0, (now - ts) / 86400)
        weights.append(1 + days_old / 365)
    return random.choices(candidates, weights=weights, k=1)[0]


def notify(title, body):
    safe_body = body.replace('"', "'").replace("\n", " ")[:200]
    subprocess.run([
        "osascript", "-e",
        f'display notification "{safe_body}" with title "{title}"',
    ], check=False)


def main():
    corpus = load_corpus()
    marks = corpus.get("marks", [])
    seen = load_history()

    chosen = pick(marks, seen)
    if chosen is None:
        reset_history()
        seen = set()
        chosen = pick(marks, seen)
        if chosen is None:
            print("No marks available.", file=sys.stderr)
            sys.exit(1)
        round_msg = "已完成全集一轮，开始新一轮"
    else:
        round_msg = ""

    append_history(chosen["bookmarkId"])

    output = {
        "round_msg": round_msg,
        "bookmarkId": chosen["bookmarkId"],
        "title": chosen.get("title", ""),
        "author": chosen.get("author", ""),
        "chapter": chosen.get("chapter", ""),
        "text": chosen.get("text", ""),
        "date": chosen.get("date", ""),
        "bookId": chosen.get("bookId", ""),
        "total_marks": len(marks),
        "shown_so_far": len(seen) + 1,
    }

    print(json.dumps(output, ensure_ascii=False, indent=2))

    if "--notify" in sys.argv:
        title = f"📖 今日回顾 · {chosen.get('title', '')}"
        notify(title, chosen.get("text", "")[:160])


if __name__ == "__main__":
    main()
