-- =====================================================================
-- 02 - CTAS: ratings partitioned by rating year (BDF_6 / BDF_7 labs)
-- 1995..2023 = 29 partitions (Athena CTAS limit is 100 per statement).
-- =====================================================================

CREATE TABLE movielens_db.ratings_by_year
WITH (
  format = 'PARQUET',
  write_compression = 'ZSTD',
  external_location = 's3://bdf-movielens-32m/ctas/ratings_by_year/',
  partitioned_by = ARRAY['rating_year']
) AS
SELECT userid,
       movieid,
       rating,
       "timestamp"                          AS rating_ts,
       year(from_unixtime("timestamp"))     AS rating_year   -- partition column goes LAST
FROM movielens_db.ratings;

SHOW PARTITIONS movielens_db.ratings_by_year;

-- ---------------------------------------------------------------------
-- EVIDENCE for the slides: run both, then copy "Data scanned" + "Run time"
-- from the Athena query details into results/athena_evidence.csv
-- ---------------------------------------------------------------------

-- E1  NOT partitioned: Athena must read the rating_year from every row
SELECT round(100.0 * avg(CASE WHEN rating >= 3.5 THEN 1 ELSE 0 END), 1) AS crowd_score_2023
FROM movielens_db.ratings
WHERE year(from_unixtime("timestamp")) = 2023;

-- E2  Partitioned: Athena opens only the folder rating_year=2023
SELECT round(100.0 * avg(CASE WHEN rating >= 3.5 THEN 1 ELSE 0 END), 1) AS crowd_score_2023
FROM movielens_db.ratings_by_year
WHERE rating_year = 2023;
