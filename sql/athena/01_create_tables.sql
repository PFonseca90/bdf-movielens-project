-- =====================================================================
-- 01 - Register the Parquet files in the Glue Data Catalog (Athena)
-- Replace YOUR-BUCKET with your bucket. Run each statement on its own.
--
-- Upload first (S3 console or CloudShell `aws s3 cp`), one folder per table:
--   Data/Parquet/ml-32m/ratings.parquet        -> s3://YOUR-BUCKET/movielens/ratings/
--   Data/Parquet/ml-32m/movies.parquet         -> s3://YOUR-BUCKET/movielens/movies/
--   Data/Parquet/ml-32m/links.parquet          -> s3://YOUR-BUCKET/movielens/links/
--   Data/Parquet/ml-32m/tags.parquet           -> s3://YOUR-BUCKET/movielens/tags/
--   Data/Parquet/external/rt_movies.parquet    -> s3://YOUR-BUCKET/external/rt_movies/
--   Data/Parquet/external/imdb_ratings.parquet -> s3://YOUR-BUCKET/external/imdb_ratings/
-- (Alternative to these DDLs: point a Glue Crawler at s3://YOUR-BUCKET/movielens/
--  and s3://YOUR-BUCKET/external/ - same result, as in the BDF_5 lab.)
-- =====================================================================

CREATE DATABASE IF NOT EXISTS movielens_db;

CREATE EXTERNAL TABLE IF NOT EXISTS movielens_db.ratings (
  userid      bigint,
  movieid     bigint,
  rating      double,
  `timestamp` bigint
)
STORED AS PARQUET
LOCATION 's3://YOUR-BUCKET/movielens/ratings/';

CREATE EXTERNAL TABLE IF NOT EXISTS movielens_db.movies (
  movieid bigint,
  title   string,
  genres  string
)
STORED AS PARQUET
LOCATION 's3://YOUR-BUCKET/movielens/movies/';

CREATE EXTERNAL TABLE IF NOT EXISTS movielens_db.links (
  movieid bigint,
  imdbid  string,
  tmdbid  bigint
)
STORED AS PARQUET
LOCATION 's3://YOUR-BUCKET/movielens/links/';

CREATE EXTERNAL TABLE IF NOT EXISTS movielens_db.tags (
  userid      bigint,
  movieid     bigint,
  tag         string,
  `timestamp` bigint
)
STORED AS PARQUET
LOCATION 's3://YOUR-BUCKET/movielens/tags/';

CREATE EXTERNAL TABLE IF NOT EXISTS movielens_db.rt_movies (
  rotten_tomatoes_link string,
  movie_title          string,
  critics_consensus    string,
  rt_genres            string,
  directors            string,
  release_date         date,
  release_year         bigint,
  tomatometer_rating   int,
  tomatometer_count    int,
  rt_audience_rating   int,
  rt_audience_count    int
)
STORED AS PARQUET
LOCATION 's3://YOUR-BUCKET/external/rt_movies/';

CREATE EXTERNAL TABLE IF NOT EXISTS movielens_db.imdb_ratings (
  tconst      string,
  imdb_rating double,
  imdb_votes  int
)
STORED AS PARQUET
LOCATION 's3://YOUR-BUCKET/external/imdb_ratings/';

-- Sanity checks (compare with the local DuckDB numbers in results/)
SELECT count(*) FROM movielens_db.ratings;        -- expect 32,000,204
SELECT count(*) FROM movielens_db.rt_movies;      -- expect 17,712
SELECT count(*) FROM movielens_db.imdb_ratings;   -- expect ~1.7M (IMDb file of Nov 2026)
