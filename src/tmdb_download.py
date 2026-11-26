# ---
# jupyter:
#   jupytext:
#     text_representation:
#       extension: .py
#       format_name: percent
#       format_version: '1.3'
#       jupytext_version: 1.19.7
#   kernelspec:
#     display_name: bdf-movielens-project (3.13.7)
#     language: python
#     name: python3
# ---

# %% [markdown]
# # TMDB API Download
#
# The canonical way to get movie information from TMDB at the moment is via a REST API using an API KEY or an Access token. A simple curl request for a movie:
#
# ```sh
# curl --request GET \
#      --url 'https://api.themoviedb.org/3/movie/11?append_to_response=videos,images' \
#      --header 'Authorization: Bearer eyJhbGciOiJIUzI1NiJ9.eyJhd...'
# ```
#
# This is implemented in Python using the `requests` library next.

# %%
from pathlib import Path


PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
    if "__file__" in globals()
    else Path.cwd().resolve().parent  # notebooks run from notebooks/
)

RAW_DIR = PROJECT_ROOT / "Data" / "Raw"
PARQUET_DIR = PROJECT_ROOT / "Data" / "Parquet"

# %%
TMDB_RAW = RAW_DIR / "TMDB"
TMDB_RAW.mkdir(parents=True, exist_ok=True)

TMDB_PARQUET = PARQUET_DIR / "TMDB"
TMDB_PARQUET.mkdir(parents=True, exist_ok=True)

# %%
import json
import os
import time
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm

API_KEY = os.getenv("TMDB_API_KEY")
if not API_KEY:
    raise RuntimeError("TMDB_API_KEY is not set (v3 API key or v4 access token)")

# v4 access tokens are JWTs and go in a header; v3 keys go in the query string.
# Prefer the header: query strings leak into logs and exception messages.
AUTH_HEADERS, AUTH_PARAMS = (
    ({"Authorization": f"Bearer {API_KEY}"}, {})
    if API_KEY.startswith("eyJ")
    else ({}, {"api_key": API_KEY})
)

LINKS_PATH = RAW_DIR / "MovieLens" / "links.csv"
OUTPUT_JSONL = TMDB_RAW / "tmdb.jsonl"
PARQUET_PATH = TMDB_PARQUET / "tmdb.parquet"

# session with automatic retries for transient network/rate-limit errors
session = requests.Session()
retries = Retry(
    total=5,
    backoff_factor=1.0,  # Waits 1s, 2s, 4s, 8s, 16s on failure
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
session.mount("https://", HTTPAdapter(max_retries=retries))

links = pd.read_csv(LINKS_PATH).dropna(subset=["tmdbId"])
all_tmdb_ids = links["tmdbId"].astype(int).unique().tolist()

# check existing progress so we can resume safely
completed_ids = set()
if os.path.exists(OUTPUT_JSONL):
    with open(OUTPUT_JSONL, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    completed_ids.add(json.loads(line)["queried_tmdb_id"])
                except (json.JSONDecodeError, KeyError):
                    # truncated last line from an interrupted run; re-fetched below
                    print("Ignoring unparseable line in existing output")

remaining_ids = [tid for tid in all_tmdb_ids if tid not in completed_ids]
print(f"Total unique TMDB IDs: {len(all_tmdb_ids)} | Already fetched: {len(completed_ids)} | Remaining: {len(remaining_ids)}")

# Fetch and append line-by-line
with open(OUTPUT_JSONL, "a", encoding="utf-8") as out_file:
    for tid in tqdm(remaining_ids, desc="Fetching TMDB metadata"):
        url = f"https://api.themoviedb.org/3/movie/{tid}"  # v3
        params = {
            **AUTH_PARAMS,
            "append_to_response": "credits,keywords,release_dates"
        }

        try:
            resp = session.get(url, params=params, headers=AUTH_HEADERS, timeout=10)

            if resp.status_code == 200:
                payload = resp.json()
                payload["queried_tmdb_id"] = tid
                payload["_status"] = "ok"
            elif resp.status_code == 404:
                # Record 404s so we don't re-query dead IDs on resume
                payload = {"queried_tmdb_id": tid, "_status": "not_found"}
            elif resp.status_code in (401, 403):
                # bad credentials fail every request; don't spam through all IDs
                raise RuntimeError(f"TMDB auth failed ({resp.status_code}): check TMDB_API_KEY")
            else:
                print(f"\nUnexpected status {resp.status_code} for ID {tid}, skipping for now.")
                continue

            out_file.write(json.dumps(payload, ensure_ascii=False) + "\n")
            out_file.flush()  # Guarantee write to disk immediately

        except requests.exceptions.RequestException as e:
            # (no secrets in the message: the key is sent via header or not logged)
            print(f"\nNetwork error on ID {tid}: {type(e).__name__}. Stop and re-run to resume.")
            break

        # ~35 requests/sec (safely below TMDB's ~40-50 req/s limit)
        time.sleep(0.028)


# %%
rows = []
with open(OUTPUT_JSONL, "r", encoding="utf-8") as f:
    for line in f:
        if not line.strip():
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue  # truncated line from an interrupted run
        if data.get("_status") != "ok":
            continue

        credits = data.get("credits") or {}
        crew = credits.get("crew") or []
        directors = [c["name"] for c in crew if c.get("job") == "Director"]
        cast = [c["name"] for c in (credits.get("cast") or [])[:5]]
        keywords = [k["name"] for k in (data.get("keywords") or {}).get("keywords") or []]
        
        rows.append({
            "tmdbId": data["queried_tmdb_id"],
            "overview": data.get("overview"),
            "tagline": data.get("tagline"),
            "release_date": data.get("release_date"),
            "runtime": data.get("runtime"),
            "budget": data.get("budget"),
            "revenue": data.get("revenue"),
            "popularity": data.get("popularity"),
            "vote_average": data.get("vote_average"),
            "vote_count": data.get("vote_count"),
            "original_language": data.get("original_language"),
            "poster_path": data.get("poster_path"),
            "directors": directors,
            "top_cast": cast,
            "keywords": keywords
        })

pd.DataFrame(rows).to_parquet(PARQUET_PATH, index=False)
