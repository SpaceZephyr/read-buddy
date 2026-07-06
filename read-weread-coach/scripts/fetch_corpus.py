#!/usr/bin/env python3
"""Fetch WeRead corpus (notebooks + bookmarks + reviews) into a cached JSON.

Skips refetch if cache is fresh (< 24h).
Usage: python3 fetch_corpus.py [--force]
"""
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path

API = "https://i.weread.qq.com/api/agent/gateway"
KEY = os.environ.get("WEREAD_API_KEY")
if not KEY:
    print("WEREAD_API_KEY not set", file=sys.stderr)
    sys.exit(1)
SKILL_VERSION = "1.0.3"
CACHE = Path("/tmp/read-weread-coach/corpus.json")
TTL = 86400


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
        except Exception:
            if attempt == 2:
                return {}
            time.sleep(1)


def fetch_notebooks():
    out, last_sort = [], None
    while True:
        p = {"api_name": "/user/notebooks", "count": 50}
        if last_sort:
            p["lastSort"] = last_sort
        r = call(p)
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
        "title": (b.get("book") or {}).get("title", ""),
        "author": (b.get("book") or {}).get("author", ""),
        "progress": b.get("readingProgress", 0),
        "bookmarks": call({"api_name": "/book/bookmarklist", "bookId": bid}),
        "reviews": call({"api_name": "/review/list/mine", "bookid": bid, "count": 100}),
    }


def main():
    force = "--force" in sys.argv
    if CACHE.exists() and not force:
        age = time.time() - CACHE.stat().st_mtime
        if age < TTL:
            print(f"Cache fresh ({int(age/3600)}h old), skip fetch", file=sys.stderr)
            return

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    print("Fetching notebooks...", file=sys.stderr)
    books = fetch_notebooks()
    print(f"  {len(books)} books", file=sys.stderr)

    data = []
    print("Fetching per-book in parallel...", file=sys.stderr)
    with ThreadPoolExecutor(max_workers=8) as ex:
        futs = [ex.submit(fetch_book, b) for b in books]
        for i, f in enumerate(as_completed(futs), 1):
            data.append(f.result())
            if i % 20 == 0:
                print(f"  {i}/{len(books)}", file=sys.stderr)

    marks, reviews = [], []
    for b in data:
        chapters = {c["chapterUid"]: c for c in (b["bookmarks"] or {}).get("chapters", []) or []}
        for m in (b["bookmarks"] or {}).get("updated", []) or []:
            text = (m.get("markText") or "").strip()
            if not text:
                continue
            ch = chapters.get(m.get("chapterUid"), {})
            marks.append({
                "bookmarkId": m.get("bookmarkId"),
                "bookId": b["bookId"],
                "title": b["title"],
                "author": b["author"],
                "chapter": ch.get("title", ""),
                "text": text,
                "createTime": m.get("createTime", 0),
                "date": datetime.fromtimestamp(m["createTime"]).strftime("%Y-%m-%d") if m.get("createTime") else "",
                "range": m.get("range", ""),
            })
        for r in (b["reviews"] or {}).get("reviews", []) or []:
            rev = r.get("review", {})
            content = (rev.get("content") or "").strip()
            if not content:
                continue
            reviews.append({
                "reviewId": rev.get("reviewId"),
                "bookId": b["bookId"],
                "title": b["title"],
                "author": b["author"],
                "chapter": rev.get("chapterName") or "",
                "content": content,
                "createTime": rev.get("createTime", 0),
                "date": datetime.fromtimestamp(rev["createTime"]).strftime("%Y-%m-%d") if rev.get("createTime") else "",
            })

    bundle = {
        "fetched_at": int(time.time()),
        "books": [{"bookId": b["bookId"], "title": b["title"], "author": b["author"], "progress": b["progress"]} for b in data],
        "marks": marks,
        "reviews": reviews,
    }
    CACHE.write_text(json.dumps(bundle, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"WROTE {CACHE}  books={len(data)} marks={len(marks)} reviews={len(reviews)}")


if __name__ == "__main__":
    main()
