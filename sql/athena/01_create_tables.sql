-- =====================================================================
-- 01 - Registered Parquet files in the Glue Data Catalog (Athena)
-- Run each statement on its own.
--
--   Data/Parquet/ml-32m/ratings.parquet        -> s3://bdf-movielens-32m/raw/ratings/
--   Data/Parquet/ml-32m/movies.parquet         -> s3://bdf-movielens-32m/raw/movies/
--   Data/Parquet/ml-32m/links.parquet          -> s3://bdf-movielens-32m/raw/links/
--   Data/Parquet/ml-32m/tags.parquet           -> s3://bdf-movielens-32m/raw/tags/
--   Data/Parquet/external/rt_movies.parquet    -> s3://bdf-movielens-32m/raw/external/rt_movies/
--   Data/Parquet/external/imdb_ratings.parquet -> s3://bdf-movielens-32m/raw/external/imdb_ratings/

-- =====================================================================

CREATE DATABASE IF NOT EXISTS movielens_db;

CREATE EXTERNAL TABLE IF NOT EXISTS movielens_db.ratings (
  userid      bigint,
  movieid     bigint,
  rating      double,
  `timestamp` bigint
)
STORED AS PARQUET
LOCATION 's3://bdf-movielens-32m/raw/ratings/';

CREATE EXTERNAL TABLE IF NOT EXISTS movielens_db.movies (
  movieid bigint,
  title   string,
  genres  string
)
STORED AS PARQUET
LOCATION 's3://bdf-movielens-32m/raw/movies/';

CREATE EXTERNAL TABLE IF NOT EXISTS movielens_db.links (
  movieid bigint,
  imdbid  string,
  tmdbid  bigint
)
STORED AS PARQUET
LOCATION 's3://bdf-movielens-32m/raw/links/';

CREATE EXTERNAL TABLE IF NOT EXISTS movielens_db.tags (
  userid      bigint,
  movieid     bigint,
  tag         string,
  `timestamp` bigint
)
STORED AS PARQUET
LOCATION 's3://bdf-movielens-32m/raw/tags/';

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
LOCATION 's3://bdf-movielens-32m/raw/external/rt_movies/';

CREATE EXTERNAL TABLE IF NOT EXISTS movielens_db.imdb_ratings (
  tconst      string,
  imdb_rating double,
  imdb_votes  int
)
STORED AS PARQUET
LOCATION 's3://bdf-movielens-32m/raw/external/imdb_ratings/';

--  checks (compare with the local DuckDB numbers in results/)
SELECT count(*) FROM movielens_db.ratings;
SELECT count(*) FROM movielens_db.rt_movies;
SELECT count(*) FROM movielens_db.imdb_ratings;
