-- Q1. What are the movie genres in the dataset?

SELECT DISTINCT
    UNNEST(string_split(genres, '|')) AS genre
FROM read_parquet('Data/Parquet/ml-32m/movies.parquet')
ORDER BY genre;


-- Q2. What is the number of movies per genre?

WITH movie_genres AS (
    SELECT
        movieId,
        UNNEST(string_split(genres, '|')) AS genre
    FROM read_parquet('Data/Parquet/ml-32m/movies.parquet')
)

SELECT
    genre,
    COUNT(*) AS total_movies
FROM movie_genres
GROUP BY genre
ORDER BY total_movies DESC;


-- Q3. What is the movie rating distribution per user?
-- Number of users by number of ratings submitted.

WITH user_ratings AS (
    SELECT
        userId,
        COUNT(*) AS rating_count
    FROM read_parquet('Data/Parquet/ml-32m/ratings.parquet')
    GROUP BY userId
)

SELECT
    rating_count AS ratings_per_user,
    COUNT(*) AS number_of_users
FROM user_ratings
GROUP BY rating_count
ORDER BY ratings_per_user;


-- Q4. What are the movies with the highest average rating?
-- Minimum 100 ratings to reduce small-sample bias.

SELECT
    m.title,
    COUNT(*) AS total_ratings,
    ROUND(AVG(r.rating), 2) AS avg_rating
FROM read_parquet('Data/Parquet/ml-32m/ratings.parquet') r
JOIN read_parquet('Data/Parquet/ml-32m/movies.parquet') m
    ON r.movieId = m.movieId
GROUP BY m.movieId, m.title
HAVING COUNT(*) >= 100
ORDER BY avg_rating DESC, total_ratings DESC
LIMIT 20;



-- Q5. What percentage of ratings belongs to the top 1% most-rated movies?

WITH movie_popularity AS (
    SELECT
        movieId,
        COUNT(*) AS rating_count
    FROM read_parquet('Data/Parquet/ml-32m/ratings.parquet')
    GROUP BY movieId
),

ranked_movies AS (
    SELECT
        movieId,
        rating_count,
        ROW_NUMBER() OVER (
            ORDER BY rating_count DESC, movieId
        ) AS popularity_rank,
        COUNT(*) OVER () AS total_movies
    FROM movie_popularity
)

SELECT
    MAX(total_movies) AS rated_movies,

    CEIL(MAX(total_movies) * 0.01)
        AS top_1_percent_movies,

    SUM(rating_count) AS total_ratings,

    SUM(
        CASE
            WHEN popularity_rank <= CEIL(total_movies * 0.01)
            THEN rating_count
            ELSE 0
        END
    ) AS top_1_percent_ratings,

    ROUND(
        100.0 * SUM(
            CASE
                WHEN popularity_rank <= CEIL(total_movies * 0.01)
                THEN rating_count
                ELSE 0
            END
        ) / SUM(rating_count),
        2
    ) AS concentration_percentage

FROM ranked_movies;
