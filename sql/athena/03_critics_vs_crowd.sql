-- =====================================================================
-- 03 - Critics vs Crowd in Athena (same logic as src/07_critics_vs_crowd.py)
--   CRITICS = Rotten Tomatoes Tomatometer (% critics positive)
--   CROWD   = % of MovieLens ratings >= 3.5 stars
--   GAP     = crowd - critics ;  RANK GAP = crowd percentile - critics percentile
-- Differences vs DuckDB:  no QUALIFY (use ROW_NUMBER in a subquery),
-- regexp back-references are $1 (not \1), no strip_accents (use normalize).
-- =====================================================================

-- C1  Crowd score per movie: the 32M-row aggregation, done once (CTAS)
CREATE TABLE movielens_db.crowd_scores
WITH (format = 'PARQUET', write_compression = 'ZSTD',
      external_location = 's3://bdf-movielens-32m/ctas/crowd_scores/') AS
SELECT movieid,
       count(*)                                                          AS n_ratings,
       round(avg(rating), 3)                                             AS avg_rating,
       round(100.0 * avg(CASE WHEN rating >= 3.5 THEN 1 ELSE 0 END), 1)  AS crowd_score
FROM movielens_db.ratings
GROUP BY movieid;

-- C2  Matched analysis table (title + year match, one-to-one)
CREATE TABLE movielens_db.critics_vs_crowd
WITH (format = 'PARQUET', write_compression = 'ZSTD',
      external_location = 's3://bdf-movielens-32m/ctas/critics_vs_crowd/') AS
WITH ml_a AS (
    SELECT movieid, title AS ml_title, genres,
           try_cast(regexp_extract(title, '\((\d{4})\)\s*$', 1) AS integer)          AS year,
           trim(regexp_replace(title, '\s*\(\d{4}\)\s*$', ''))                      AS t1
    FROM movielens_db.movies
), ml_b AS (
    SELECT *, trim(regexp_replace(regexp_replace(t1, '\s*\([^)]*\)\s*$', ''), '\s*\([^)]*\)\s*$', '')) AS t2
    FROM ml_a
), ml AS (
    SELECT movieid, ml_title, genres, year,
           regexp_replace(t2, '^(.+), (The|A|An|Les|La|Le|L''|Il|El|Das|Der|Die)$', '$2 $1') AS clean_title
    FROM ml_b
), ml_key AS (
    SELECT *, regexp_replace(replace(lower(regexp_replace(normalize(clean_title, NFD), '\p{M}', '')), '&', 'and'), '[^a-z0-9]', '') AS title_key
    FROM ml
), rt AS (
    SELECT *, regexp_replace(replace(lower(regexp_replace(normalize(
                  regexp_replace(movie_title, '\s*\(\d{4}\)\s*$', ''), NFD), '\p{M}', '')), '&', 'and'), '[^a-z0-9]', '') AS title_key
    FROM movielens_db.rt_movies
    WHERE tomatometer_rating IS NOT NULL AND release_year IS NOT NULL
), cand AS (
    SELECT m.movieid, r.rotten_tomatoes_link, abs(m.year - r.release_year) AS year_diff,
           row_number() OVER (PARTITION BY m.movieid
                              ORDER BY abs(m.year - r.release_year), r.tomatometer_count DESC) AS rn_ml
    FROM ml_key m
    JOIN rt r ON m.title_key = r.title_key AND abs(m.year - r.release_year) <= 1
), best AS (
    SELECT movieid, rotten_tomatoes_link, year_diff,
           row_number() OVER (PARTITION BY rotten_tomatoes_link ORDER BY year_diff, movieid) AS rn_rt
    FROM cand WHERE rn_ml = 1
), joined AS (
    SELECT m.movieid, m.clean_title AS title, m.year, m.genres,
           c.n_ratings, c.avg_rating, c.crowd_score,
           r.tomatometer_rating AS critics_score, r.tomatometer_count AS critic_reviews,
           r.rt_audience_rating, i.imdb_rating, i.imdb_votes,
           round(c.crowd_score - r.tomatometer_rating, 1) AS gap,
           r.directors, b.year_diff
    FROM best b
    JOIN ml_key m                   ON m.movieid = b.movieid
    JOIN rt r                       ON r.rotten_tomatoes_link = b.rotten_tomatoes_link
    JOIN movielens_db.crowd_scores c ON c.movieid = b.movieid
    LEFT JOIN movielens_db.links l  ON l.movieid = b.movieid
    LEFT JOIN movielens_db.imdb_ratings i ON i.tconst = 'tt' || lpad(l.imdbid, 7, '0')
    WHERE b.rn_rt = 1 AND c.n_ratings >= 100 AND r.tomatometer_count >= 20
)
SELECT *,
       round(100 * percent_rank() OVER (ORDER BY crowd_score), 1)   AS crowd_pct,
       round(100 * percent_rank() OVER (ORDER BY critics_score), 1) AS critics_pct
FROM joined;

-- Q1  How many films? (local DuckDB: 6,932)
SELECT count(*) AS movies, round(avg(critics_score), 1) AS avg_critics,
       round(avg(crowd_score), 1) AS avg_crowd, round(corr(crowd_score, critics_score), 3) AS correlation
FROM movielens_db.critics_vs_crowd;

-- Q2  Genre battle (rank gap per genre)
SELECT genre, count(*) AS movies,
       round(avg(critics_score), 1) AS avg_critics,
       round(avg(crowd_score), 1)   AS avg_crowd,
       round(avg(crowd_pct - critics_pct), 1) AS avg_rank_gap
FROM movielens_db.critics_vs_crowd
CROSS JOIN UNNEST(split(genres, '|')) AS t(genre)
WHERE genre NOT IN ('(no genres listed)', 'IMAX')
GROUP BY genre
HAVING count(*) >= 30
ORDER BY avg_rank_gap DESC;

-- Q3  Hall of Shame: crowd loved, critics hated (famous films)
SELECT title, year, n_ratings, crowd_score, critics_score, gap,
       round(crowd_pct - critics_pct, 1) AS rank_gap
FROM movielens_db.critics_vs_crowd
WHERE n_ratings >= 10000 AND critic_reviews >= 40
ORDER BY rank_gap DESC
LIMIT 10;

-- Q4  Hall of Shame: critics loved, crowd hated
SELECT title, year, n_ratings, crowd_score, critics_score, gap,
       round(crowd_pct - critics_pct, 1) AS rank_gap
FROM movielens_db.critics_vs_crowd
WHERE n_ratings >= 10000 AND critic_reviews >= 40
ORDER BY rank_gap ASC
LIMIT 10;

-- Q5  Gap by release decade
SELECT (year / 10) * 10 AS decade, count(*) AS movies,
       round(avg(critics_score), 1) AS avg_critics, round(avg(crowd_score), 1) AS avg_crowd,
       round(avg(crowd_pct - critics_pct), 1) AS avg_rank_gap
FROM movielens_db.critics_vs_crowd
WHERE year >= 1930
GROUP BY 1 ORDER BY 1;
