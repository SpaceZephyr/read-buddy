#!/usr/bin/env python3
"""Fetch all WeRead data needed for analysis into a single JSON file.

Usage: python3 fetch.py <output_json_path>
"""
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

API = "https://i.weread.qq.com/api/agent/gateway"
KEY = os.environ.get("WEREAD_API_KEY")
if not KEY:
    print("WEREAD_API_KEY not set", file=sys.stderr)
    sys.exit(1)
SKILL_VERSION = "1.0.3"


def call(payload):
    body = json.dumps({**payload, "skill_version": SKILL_VERSION}).encode()
    req = urllib.request.Request(
        API, data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 2:
                return {"_error": str(e)}
            time.sleep(1)


def fetch_notebooks():
    out = []
    last_sort = None
    while True:
        payload = {"api_name": "/user/notebooks", "count": 50}
        if last_sort:
            payload["lastSort"] = last_sort
        r = call(payload)
        books = r.get("books", [])
        out.extend(books)
        if r.get("hasMore") != 1 or not books:
            break
        last_sort = books[-1].get("sort")
    return out


def fetch_book(b):
    bid = b["bookId"]
    return {
        "bookId": bid,
        "meta": b,
        "bookmarks": call({"api_name": "/book/bookmarklist", "bookId": bid}),
        "reviews": call({"api_name": "/review/list/mine", "bookid": bid, "count": 100}),
    }


def main():
    out_path = Path(sys.argv[1])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print("Fetching notebooks...", file=sys.stderr)
    books = fetch_notebooks()
    print(f"  {len(books)} books", file=sys.stderr)

    print("Fetching shelf...", file=sys.stderr)
    shelf = call({"api_name": "/shelf/sync"})

    print("Fetching readdata (annual)...", file=sys.stderr)
    import time as _t
    now = int(_t.time())
    one_year_ago = now - 365 * 86400
    readdata_current = call({"api_name": "/readdata/detail", "mode": "annually"})
    readdata_prev = call({"api_name": "/readdata/detail", "mode": "annually", "baseTime": one_year_ago})
    readdata_overall = call({"api_name": "/readdata/detail", "mode": "overall"})

    print(f"Fetching {len(books)} books in parallel...", file=sys.stderr)
    book_data = []
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(fetch_book, b): b for b in books}
        for i, f in enumerate(as_completed(futs), 1):
            book_data.append(f.result())
            if i % 20 == 0:
                print(f"  {i}/{len(books)}", file=sys.stderr)

    bundle = {
        "fetched_at": now,
        "notebooks_count": len(books),
        "shelf": shelf,
        "readdata": {
            "current_year": readdata_current,
            "previous_year": readdata_prev,
            "overall": readdata_overall,
        },
        "books": book_data,
    }

    out_path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    total_marks = sum(len((b.get("bookmarks") or {}).get("updated", []) or []) for b in book_data)
    total_reviews = sum(len((b.get("reviews") or {}).get("reviews", []) or []) for b in book_data)
    print(f"\nWROTE {out_path}")
    print(f"books={len(books)} marks={total_marks} reviews={total_reviews}")


if __name__ == "__main__":
    main()
