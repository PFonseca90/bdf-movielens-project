#!/usr/bin/env python3
"""
Read tmdbId values from MovieLens links.csv, fetch each movie from the
TMDB API, and append one JSON object per line to a JSONL file.

- Re-runnable: IDs already in the output file (or the errors file) are skipped.
- Rate-limited and retried (429 / 5xx) so a long run doesn't get blocked.

Usage:
    export TMDB_TOKEN="<your TMDB API Read Access Token>"
    python3 tmdb_fetch.py links.csv tmdb_movies.jsonl
"""
import csv
import json
import os
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = os.environ.get("TMDB_BASE_URL", "https://api.themoviedb.org/3")
TOKEN = os.environ["TMDB_TOKEN"]          # fail fast if the token isn't set
WORKERS = 8                               # parallel requests in flight
MAX_RPS = 20                              # stay well under TMDB's limit
# Extra data in the same call, e.g. "credits,keywords,external_ids".
# Leave empty for movie details only (smaller records).
APPEND = os.environ.get("TMDB_APPEND", "")


def read_tmdb_ids(path):
    """Unique, non-empty tmdbId values from links.csv, in file order."""
    ids = []
    seen = set()
    with open(path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            raw = (row.get("tmdbId") or "").strip()
            if not raw:
                continue                  # some MovieLens rows have no TMDB ID
            tmdb_id = int(float(raw))     # handles "862" and "862.0"
            if tmdb_id not in seen:
                seen.add(tmdb_id)
                ids.append(tmdb_id)
    return ids


def already_done(*paths):
    """IDs already written to the output or errors file (for resuming)."""
    done = set()
    for path in paths:
        if os.path.exists(path):
            with open(path, encoding="utf-8") as f:
                for line in f:
                    try:
                        done.add(int(json.loads(line)["id"]))
                    except (ValueError, KeyError):
                        pass              # ignore a half-written last line
    return done


class RateLimiter:
    """Allow at most `rps` calls per second across all threads."""

    def __init__(self, rps):
        self.interval = 1.0 / rps
        self.lock = threading.Lock()
        self.next_time = time.monotonic()

    def wait(self):
        with self.lock:
            now = time.monotonic()
            if self.next_time > now:
                time.sleep(self.next_time - now)
            self.next_time = max(self.next_time, now) + self.interval


def make_session():
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=1,                 # 1s, 2s, 4s, ...
        status_forcelist=[429, 500, 502, 503, 504],
        respect_retry_after_header=True,
        allowed_methods=["GET"],
    )
    session.mount("https://", HTTPAdapter(max_retries=retry, pool_maxsize=WORKERS))
    session.mount("http://", HTTPAdapter(max_retries=retry, pool_maxsize=WORKERS))
    session.headers.update({
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/json",
    })
    return session


def fetch(session, limiter, tmdb_id):
    """Return (tmdb_id, movie_dict or None, error_message or None)."""
    limiter.wait()
    params = {"append_to_response": APPEND} if APPEND else None
    try:
        resp = session.get(f"{BASE_URL}/movie/{tmdb_id}", params=params, timeout=30)
    except requests.RequestException as exc:
        return tmdb_id, None, str(exc)
    if resp.status_code == 200:
        return tmdb_id, resp.json(), None
    return tmdb_id, None, f"HTTP {resp.status_code}"   # e.g. 404 = removed from TMDB


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: tmdb_fetch.py <links.csv> <output.jsonl>")
    links_path, out_path = sys.argv[1], sys.argv[2]
    err_path = out_path + ".errors"

    ids = read_tmdb_ids(links_path)
    done = already_done(out_path, err_path)
    todo = [i for i in ids if i not in done]
    print(f"{len(ids)} TMDB IDs, {len(done)} already done, {len(todo)} to fetch")

    session = make_session()
    limiter = RateLimiter(MAX_RPS)
    ok = failed = 0
    start = time.monotonic()

    # Only the main thread writes, so the files never get interleaved lines.
    with open(out_path, "a", encoding="utf-8") as out, \
         open(err_path, "a", encoding="utf-8") as err, \
         ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(fetch, session, limiter, i) for i in todo]
        for n, fut in enumerate(as_completed(futures), 1):
            tmdb_id, movie, error = fut.result()
            if movie is not None:
                out.write(json.dumps(movie, ensure_ascii=False) + "\n")
                ok += 1
            else:
                err.write(json.dumps({"id": tmdb_id, "error": error}) + "\n")
                failed += 1
            if n % 1000 == 0:
                out.flush()
                err.flush()
                rate = n / (time.monotonic() - start)
                print(f"{n}/{len(todo)}  ok={ok} failed={failed}  {rate:.1f}/s", flush=True)

    print(f"Finished: ok={ok} failed={failed}. Output: {out_path}, errors: {err_path}")


if __name__ == "__main__":
    main()
