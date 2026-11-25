"""
07 - Critics vs Crowd: who was right?

Question: For which movies (and which genres) do professional critics and
regular viewers disagree the most?

  CRITICS = Rotten Tomatoes Tomatometer  -> % of critics with a positive review
  CROWD   = MovieLens 32M ratings        -> % of ratings >= 3.5 stars
            (the same rule Rotten Tomatoes uses for its own audience score,
             so both numbers are "% who liked it", 0-100: apples to apples)
  GAP     = crowd - critics
            positive -> crowd liked it more  ("Popcorn Person")
            negative -> critics liked it more ("Film Snob")
  RANK GAP = crowd percentile - critics percentile  (-100 .. +100)
            MovieLens users are stricter graders than critics on average
            (crowd ~54 vs critics ~62), so the raw gap is negative for almost
            every film. Comparing RANKS ("critics put it in their top 10%,
            the crowd in its bottom 20%") removes that scale difference.
            The rank gap is the main measure for Hall of Shame + Genre Battle.

Joins
  MovieLens -> IMDb  : exact, through links.imdbId  (tt + 7 digits)
  MovieLens -> RT    : normalised title + release year (+-1 year), one-to-one

Input : Data/Parquet/ml-32m/*.parquet  (from 01_data_ingestion_32m.py)
        Data/Parquet/external/*.parquet (from 06_ingest_external.py)
Output: Data/Parquet/analysis/critics_vs_crowd.parquet
        results/critics_vs_crowd/*.csv
"""
from pathlib import Path
from time import perf_counter
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ML = PROJECT_ROOT / "Data" / "Parquet" / "ml-32m"
EXT = PROJECT_ROOT / "Data" / "Parquet" / "external"
ANALYSIS = PROJECT_ROOT / "Data" / "Parquet" / "analysis"
RESULTS = PROJECT_ROOT / "results" / "critics_vs_crowd"
ANALYSIS.mkdir(parents=True, exist_ok=True)
RESULTS.mkdir(parents=True, exist_ok=True)

# Thresholds (kept in one place so they are easy to explain on a slide)
MIN_ML_RATINGS = 100        # crowd score must rest on >= 100 MovieLens ratings
MIN_CRITIC_REVIEWS = 20     # tomatometer must rest on >= 20 critic reviews
FAMOUS_ML_RATINGS = 10000   # "everybody knows it" level, for Hall of Shame / quiz
FAMOUS_CRITIC_REVIEWS = 40

con = duckdb.connect()
con.sql("SET memory_limit = '2GB'")
con.sql(f"SET temp_directory = '{(PROJECT_ROOT / '.duckdb_tmp').as_posix()}'")

def p(path: Path) -> str:
    return path.as_posix()

def save(sql: str, name: str):
    df = con.sql(sql).df()
    df.to_csv(RESULTS / f"{name}.csv", index=False)
    print(f"\n[{name}.csv] {len(df)} rows")
    print(df.head(20).to_string(index=False))
    return df

t0 = perf_counter()

# ------------------------------------------------------------------
# 1. CROWD score per movie, from the 32M ratings (the big-data step)
# ------------------------------------------------------------------
con.sql(f"""
    CREATE TABLE crowd AS
    SELECT movieId,
           COUNT(*)                                       AS n_ratings,
           ROUND(AVG(rating), 3)                          AS avg_rating,
           ROUND(100.0 * AVG(CASE WHEN rating >= 3.5 THEN 1 ELSE 0 END), 1) AS crowd_score
    FROM read_parquet('{p(ML / "ratings.parquet")}')
    GROUP BY movieId
""")
print(f"Step 1 crowd scores from 32M ratings: {perf_counter() - t0:.1f}s")

# ------------------------------------------------------------------
# 2. Clean MovieLens titles:  "Matrix, The (1999)" -> "The Matrix", 1999
# ------------------------------------------------------------------
# Title key = lowercase, no accents, '&' -> 'and', only letters+digits.
KEY = "regexp_replace(replace(lower(strip_accents({x})), '&', 'and'), '[^a-z0-9]', '', 'g')"
ML_KEY = KEY.format(x="clean_title")

con.sql(f"""
    CREATE TABLE ml_movies AS
    WITH a AS (
        SELECT m.movieId, m.title AS ml_title, m.genres,
               TRY_CAST(regexp_extract(m.title, '\\((\\d{{4}})\\)\\s*$', 1) AS INTEGER) AS year,
               trim(regexp_replace(m.title, '\\s*\\(\\d{{4}}\\)\\s*$', ''))               AS t1
        FROM read_parquet('{p(ML / "movies.parquet")}') m
    ), b AS (   -- drop alternative titles in brackets: "City of Lost Children, The (Cité des...)"
        SELECT *, trim(regexp_replace(regexp_replace(t1, '\\s*\\([^)]*\\)\\s*$', ''),
                                      '\\s*\\([^)]*\\)\\s*$', '')) AS t2
        FROM a
    ), c AS (   -- move trailing article to the front: "Matrix, The" -> "The Matrix"
        SELECT *, regexp_replace(t2, '^(.+), (The|A|An|Les|La|Le|L''|Il|El|Das|Der|Die)$', '\\2 \\1') AS clean_title
        FROM b
    )
    SELECT movieId, ml_title, clean_title, year, genres,
           {ML_KEY} AS title_key
    FROM c
""")

RT_KEY = KEY.format(x="regexp_replace(movie_title, '\\s*\\(\\d{4}\\)\\s*$', '')")
con.sql(f"""
    CREATE TABLE rt AS
    SELECT *, {RT_KEY} AS title_key
    FROM read_parquet('{p(EXT / "rt_movies.parquet")}')
    WHERE tomatometer_rating IS NOT NULL AND release_year IS NOT NULL
""")

# ------------------------------------------------------------------
# 3. Match MovieLens <-> Rotten Tomatoes on title key + year (+-1)
#    Keep a strict one-to-one match: best candidate per ML movie,
#    then best ML movie per RT movie (exact year first).
# ------------------------------------------------------------------
con.sql("""
    CREATE TABLE match AS
    WITH cand AS (
        SELECT m.movieId, r.rotten_tomatoes_link,
               ABS(m.year - r.release_year) AS year_diff,
               r.tomatometer_count
        FROM ml_movies m
        JOIN rt r ON m.title_key = r.title_key
                 AND ABS(m.year - r.release_year) <= 1
    ), best_per_ml AS (
        SELECT * FROM cand
        QUALIFY ROW_NUMBER() OVER (PARTITION BY movieId
                 ORDER BY year_diff, tomatometer_count DESC NULLS LAST) = 1
    )
    SELECT * FROM best_per_ml
    QUALIFY ROW_NUMBER() OVER (PARTITION BY rotten_tomatoes_link
             ORDER BY year_diff, movieId) = 1
""")

# ------------------------------------------------------------------
# 4. One analysis table: MovieLens + crowd + RT critics + IMDb
# ------------------------------------------------------------------
con.sql(f"""
    CREATE TABLE cvc_raw AS
    SELECT m.movieId, m.clean_title AS title, m.year, m.genres,
           c.n_ratings, c.avg_rating, c.crowd_score,
           r.tomatometer_rating AS critics_score, r.tomatometer_count AS critic_reviews,
           r.rt_audience_rating, r.rt_audience_count,
           i.imdb_rating, i.imdb_votes,
           ROUND(c.crowd_score - r.tomatometer_rating, 1) AS gap,
           r.critics_consensus, r.directors, r.rotten_tomatoes_link, x.year_diff,
           'tt' || lpad(CAST(l.imdbId AS VARCHAR), 7, '0') AS imdb_id
    FROM match x
    JOIN ml_movies m ON m.movieId = x.movieId
    JOIN rt r        ON r.rotten_tomatoes_link = x.rotten_tomatoes_link
    JOIN crowd c     ON c.movieId = x.movieId
    LEFT JOIN read_parquet('{p(ML / "links.parquet")}') l ON l.movieId = x.movieId
    LEFT JOIN read_parquet('{p(EXT / "imdb_ratings.parquet")}') i
           ON i.tconst = 'tt' || lpad(CAST(l.imdbId AS VARCHAR), 7, '0')
    WHERE c.n_ratings >= {MIN_ML_RATINGS} AND r.tomatometer_count >= {MIN_CRITIC_REVIEWS}
""")
# Percentile of each film inside the analysis set (0 = lowest, 100 = highest)
con.sql("""
    CREATE TABLE cvc AS
    SELECT *, ROUND(crowd_pct - critics_pct, 1) AS rank_gap
    FROM (
        SELECT *,
               ROUND(100 * PERCENT_RANK() OVER (ORDER BY crowd_score), 1)   AS crowd_pct,
               ROUND(100 * PERCENT_RANK() OVER (ORDER BY critics_score), 1) AS critics_pct
        FROM cvc_raw
    )
""")
con.sql(f"COPY cvc TO '{p(ANALYSIS / 'critics_vs_crowd.parquet')}' (FORMAT PARQUET, COMPRESSION ZSTD)")
con.sql("SELECT * EXCLUDE (critics_consensus) FROM cvc ORDER BY rank_gap DESC").df() \
   .to_csv(RESULTS / "movies_critics_vs_crowd.csv", index=False)
print(f"\nAnalysis table built: {perf_counter() - t0:.1f}s total")

# ------------------------------------------------------------------
# 5. Results
# ------------------------------------------------------------------
# 5a. Funnel: how many movies survive each step (honest about matching)
save(f"""
    SELECT 'MovieLens movies'                       AS step, COUNT(*) AS movies FROM ml_movies
    UNION ALL SELECT 'MovieLens movies with ratings', COUNT(*) FROM crowd
    UNION ALL SELECT 'Rotten Tomatoes movies (with score + year)', COUNT(*) FROM rt
    UNION ALL SELECT 'Matched MovieLens <-> RT (title+year)', COUNT(*) FROM match
    UNION ALL SELECT 'Matched with exact same year', COUNT(*) FROM match WHERE year_diff = 0
    UNION ALL SELECT 'Analysis set (>= {MIN_ML_RATINGS} ML ratings, >= {MIN_CRITIC_REVIEWS} reviews)', COUNT(*) FROM cvc
    UNION ALL SELECT 'Analysis set with IMDb rating', COUNT(imdb_rating) FROM cvc
""", "match_funnel")

# 5b. Do the different "voices" agree? (Pearson correlation)
save("""
    SELECT 'MovieLens crowd vs RT critics'      AS pair, ROUND(CORR(crowd_score, critics_score), 3) AS correlation, COUNT(*) AS movies FROM cvc
    UNION ALL SELECT 'MovieLens crowd vs RT audience', ROUND(CORR(crowd_score, rt_audience_rating), 3), COUNT(rt_audience_rating) FROM cvc
    UNION ALL SELECT 'MovieLens crowd vs IMDb rating', ROUND(CORR(crowd_score, imdb_rating), 3), COUNT(imdb_rating) FROM cvc
    UNION ALL SELECT 'RT audience vs RT critics',      ROUND(CORR(rt_audience_rating, critics_score), 3), COUNT(rt_audience_rating) FROM cvc
    UNION ALL SELECT 'IMDb rating vs RT critics',      ROUND(CORR(imdb_rating, critics_score), 3), COUNT(imdb_rating) FROM cvc
""", "voice_correlations")

# 5c. Overall picture
save("""
    SELECT COUNT(*) AS movies,
           ROUND(AVG(critics_score), 1) AS avg_critics,
           ROUND(AVG(crowd_score), 1)   AS avg_crowd,
           ROUND(AVG(rt_audience_rating), 1) AS avg_rt_audience,
           ROUND(AVG(imdb_rating) * 10, 1)   AS avg_imdb_x10,
           ROUND(AVG(gap), 1)           AS avg_gap,
           ROUND(100.0 * AVG(CASE WHEN ABS(rank_gap) <= 20 THEN 1 ELSE 0 END), 1) AS pct_rank_agree_within_20,
           ROUND(100.0 * AVG(CASE WHEN ABS(gap) <= 10 THEN 1 ELSE 0 END), 1) AS pct_agree_within_10pts,
           ROUND(100.0 * AVG(CASE WHEN gap > 10 THEN 1 ELSE 0 END), 1)       AS pct_crowd_higher,
           ROUND(100.0 * AVG(CASE WHEN gap < -10 THEN 1 ELSE 0 END), 1)      AS pct_critics_higher
    FROM cvc
""", "overall_summary")

# 5d. Genre battle: average gap per genre (a movie counts in each of its genres)
save(f"""
    WITH g AS (
        SELECT *, UNNEST(string_split(genres, '|')) AS genre FROM cvc
    ), agg AS (
        SELECT genre, COUNT(*) AS movies,
               ROUND(AVG(critics_score), 1) AS avg_critics,
               ROUND(AVG(crowd_score), 1)   AS avg_crowd,
               ROUND(AVG(gap), 1)           AS avg_gap,
               ROUND(AVG(rank_gap), 1)      AS avg_rank_gap
        FROM g
        WHERE genre NOT IN ('(no genres listed)', 'IMAX')
        GROUP BY genre HAVING COUNT(*) >= 30
    ), example AS (   -- the famous film that best shows the genre's direction
        SELECT g.genre, g.title, g.year, g.rank_gap,
               ROW_NUMBER() OVER (PARTITION BY g.genre
                   ORDER BY CASE WHEN a.avg_rank_gap >= 0 THEN g.rank_gap ELSE -g.rank_gap END DESC) AS rk
        FROM g JOIN agg a USING (genre)
        WHERE g.n_ratings >= {FAMOUS_ML_RATINGS}
    )
    SELECT a.*, e.title AS example_title, e.year AS example_year, e.rank_gap AS example_rank_gap
    FROM agg a LEFT JOIN example e ON e.genre = a.genre AND e.rk = 1
    ORDER BY avg_rank_gap DESC
""", "genre_gap")

# 5e. Hall of Shame: biggest gaps among movies everybody knows
for side, order in [("crowd_loved", "rank_gap DESC"), ("critics_loved", "rank_gap ASC")]:
    save(f"""
        SELECT title, year, genres, n_ratings, crowd_score, critics_score, gap,
               crowd_pct, critics_pct, rank_gap, imdb_rating, rt_audience_rating
        FROM cvc
        WHERE n_ratings >= {FAMOUS_ML_RATINGS} AND critic_reviews >= {FAMOUS_CRITIC_REVIEWS}
        ORDER BY {order} LIMIT 15
    """, f"hall_of_shame_{side}")

# 5f. Does the gap change with the movie's age? (release decade)
save("""
    SELECT (year // 10) * 10 AS decade, COUNT(*) AS movies,
           ROUND(AVG(critics_score), 1) AS avg_critics,
           ROUND(AVG(crowd_score), 1)   AS avg_crowd,
           ROUND(AVG(gap), 1)           AS avg_gap,
           ROUND(AVG(rank_gap), 1)      AS avg_rank_gap
    FROM cvc WHERE year >= 1930
    GROUP BY 1 ORDER BY 1
""", "gap_by_decade")

# 5g. Popularity: are crowd-pleasers more watched? (gap vs number of ratings)
save("""
    SELECT CASE WHEN n_ratings < 500   THEN '1) 100-499'
                WHEN n_ratings < 2000  THEN '2) 500-1,999'
                WHEN n_ratings < 10000 THEN '3) 2,000-9,999'
                WHEN n_ratings < 30000 THEN '4) 10,000-29,999'
                ELSE '5) 30,000+' END AS ml_ratings_bucket,
           COUNT(*) AS movies,
           ROUND(AVG(critics_score), 1) AS avg_critics,
           ROUND(AVG(crowd_score), 1)   AS avg_crowd,
           ROUND(AVG(gap), 1)           AS avg_gap,
           ROUND(AVG(rank_gap), 1)      AS avg_rank_gap
    FROM cvc GROUP BY 1 ORDER BY 1
""", "gap_by_popularity")

print(f"\nDone in {perf_counter() - t0:.1f}s. CSVs in {RESULTS}")
