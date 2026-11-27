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

# %%
import duckdb

RATINGS = "../Data/Parquet/MovieLens/ratings.parquet"
MOVIES = "../Data/Parquet/MovieLens/movies.parquet"

# The "Nostalgia Effect": do users rate older classics (e.g., 1970s films) higher
# than modern releases simply because only dedicated fans seek out older movies?
# Plan:
#   1) Average rating by movie release decade (raw nostalgia signal)
#   2) Control for the "dedicated fans" hypothesis: within the SAME popularity
#      bucket (rating count), do old movies still beat new ones? If the old-movie
#      advantage disappears once popularity is matched, the effect is driven by
#      self-selection, not intrinsic quality.

# MovieLens titles look like "Toy Story (1995)" -- pull the release year from the title.
# Shared view: every rating joined to its movie's era (movies without a year are dropped).
duckdb.sql(f"""
CREATE OR REPLACE TEMP VIEW df AS
SELECT
    r.movieId,
    r.rating,
    m.release_year,
    CASE
        WHEN m.release_year < 1970 THEN 'pre-1970'
        WHEN m.release_year < 1980 THEN '1970s'
        WHEN m.release_year < 1990 THEN '1980s'
        WHEN m.release_year < 2000 THEN '1990s'
        ELSE '2000s+'
    END AS era
FROM read_parquet('{RATINGS}') r
JOIN (
    SELECT movieId,
           TRY_CAST(regexp_extract(title, '\\((\\d{{4}})\\)\\s*$', 1) AS INTEGER) AS release_year
    FROM read_parquet('{MOVIES}')
) m USING (movieId)
WHERE m.release_year IS NOT NULL
""")

# --- Step 1: raw average rating by release decade ---
# vs_baseline compares each era with the all-time average over ALL ratings.
era_stats = duckdb.sql(f"""
WITH baseline AS (
    SELECT avg(rating) AS C FROM read_parquet('{RATINGS}')
)
SELECT
    era,
    count(*) AS n_ratings,
    count(DISTINCT movieId) AS n_movies,
    round(avg(rating), 3) AS avg_rating,
    round(avg(rating) - any_value(C), 3) AS vs_baseline
FROM df CROSS JOIN baseline
GROUP BY era
ORDER BY era
""").df()
era_stats

# --- Step 2: control for popularity (the "dedicated fans" hypothesis) ---
# Bucket every MOVIE by how many ratings it received, then compare old vs. new
# movies inside the same bucket. If only die-hard fans rate 1970s films, old films
# should cluster in low-count buckets; matching counts isolates the era effect.
pop_ctrl = duckdb.sql("""
WITH movie_pop AS (
    SELECT
        movieId, era, release_year,
        count(*) AS v,
        avg(rating) AS R,
        CASE
            WHEN count(*) < 10 THEN '<10 ratings'
            WHEN count(*) < 50 THEN '10-49'
            WHEN count(*) < 200 THEN '50-199'
            ELSE '200+'
        END AS popularity
    FROM df
    GROUP BY movieId, era, release_year
)
SELECT
    popularity, era,
    round(avg(R), 3) AS avg_rating,
    count(*) AS n_movies
FROM movie_pop
GROUP BY popularity, era
ORDER BY popularity, era
""").df()
pop_ctrl

