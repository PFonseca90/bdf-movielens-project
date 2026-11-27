-- BIG DATA FOUNDATIONS | AWS ATHENA QUERIES
-- Database: moviesdb01 | Region: us-east-1
-- Run each query separately in Athena.
-- Source data: MovieLens 32M and MovieLens 1B synthetic train shards.
-- Query result reuse must be disabled when benchmarking.

-- Q3: Distribution of the number of ratings per user (MovieLens 32M)
WITH user_ratings AS (
    SELECT userid, COUNT(*) AS rating_count
    FROM moviesdb01.crawler_ratings
    GROUP BY userid
)
SELECT rating_count AS ratings_per_user,
       COUNT(*) AS number_of_users
FROM user_ratings
GROUP BY rating_count
ORDER BY ratings_per_user;

-- Q4: Highest average rated movies (min. 100 ratings, MovieLens 32M)
SELECT m.title,
       COUNT(*) AS total_ratings,
       ROUND(AVG(r.rating), 2) AS avg_rating
FROM moviesdb01.crawler_ratings r
JOIN moviesdb01.crawler_movies m ON r.movieid = m.movieid
GROUP BY m.movieid, m.title
HAVING COUNT(*) >= 100
ORDER BY avg_rating DESC, total_ratings DESC
LIMIT 20;

-- Q5: Long-tail concentration (MovieLens 32M)
WITH movie_popularity AS (
    SELECT movieid, COUNT(*) AS rating_count
    FROM moviesdb01.crawler_ratings
    GROUP BY movieid
),
ranked_movies AS (
    SELECT movieid, rating_count,
           ROW_NUMBER() OVER (ORDER BY rating_count DESC, movieid) AS popularity_rank,
           COUNT(*) OVER () AS total_movies
    FROM movie_popularity
)
SELECT MAX(total_movies) AS rated_movies,
       CEIL(MAX(total_movies) * 0.01) AS top_1_percent_movies,
       SUM(rating_count) AS total_ratings,
       SUM(CASE WHEN popularity_rank <= CEIL(total_movies * 0.01)
                THEN rating_count ELSE 0 END) AS top_1_percent_ratings,
       ROUND(100.0 * SUM(CASE WHEN popularity_rank <= CEIL(total_movies * 0.01)
                              THEN rating_count ELSE 0 END) / SUM(rating_count), 2)
           AS concentration_percentage
FROM ranked_movies;

-- 1B: Full synthetic training dataset - same group/order/limit as local DuckDB
SELECT itemid, COUNT(*) AS interactions
FROM moviesdb01.movielens_1b_train
GROUP BY itemid
ORDER BY interactions DESC, itemid
LIMIT 10;

-- Optional 1B row-count and identifier validation (separate workload; not benchmark)
SELECT COUNT(*) AS total_interactions,
       COUNT(DISTINCT userid) AS total_users,
       MIN(itemid) AS min_item_id,
       MAX(itemid) AS max_item_id
FROM moviesdb01.movielens_1b_train;
