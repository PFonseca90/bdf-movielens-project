from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARQUET_DIR = PROJECT_ROOT / "Data" / "Parquet"

con = duckdb.connect()

# Views, para não repetir read_parquet em todas as queries
for name in ["movies", "ratings", "tags", "links"]:
    path = (PARQUET_DIR / f"{name}.parquet").as_posix()
    con.sql(f"CREATE VIEW {name} AS SELECT * FROM read_parquet('{path}')")


# Q1. What are the movie genres in the dataset?
print("\n--- Q1: GENRES ---")

genres = con.sql("""
    SELECT DISTINCT genre
    FROM movies, UNNEST(STRING_SPLIT(genres, '|')) AS t(genre)
    ORDER BY genre
""").df()

print(genres.to_string(index=False))


# Q2. Number of movies per genre
print("\n--- Q2: MOVIES PER GENRE ---")

movies_per_genre = con.sql("""
    SELECT genre, COUNT(*) AS n_movies
    FROM movies, UNNEST(STRING_SPLIT(genres, '|')) AS t(genre)
    GROUP BY genre
    ORDER BY n_movies DESC
""").df()

print(movies_per_genre.to_string(index=False))


# Q3. Rating distribution per user
print("\n--- Q3a: NUMBER OF RATINGS PER USER ---")

ratings_per_user = con.sql("""
    WITH per_user AS (
        SELECT userId, COUNT(*) AS n_ratings
        FROM ratings
        GROUP BY userId
    )
    SELECT
        COUNT(*)                        AS n_users,
        MIN(n_ratings)                  AS min_ratings,
        QUANTILE_CONT(n_ratings, 0.25)  AS p25,
        MEDIAN(n_ratings)               AS median_ratings,
        ROUND(AVG(n_ratings), 1)        AS mean_ratings,
        QUANTILE_CONT(n_ratings, 0.75)  AS p75,
        QUANTILE_CONT(n_ratings, 0.99)  AS p99,
        MAX(n_ratings)                  AS max_ratings
    FROM per_user
""").df()

print(ratings_per_user.to_string(index=False))

print("\n--- Q3b: DISTRIBUTION OF AVERAGE RATING PER USER ---")

avg_rating_per_user = con.sql("""
    WITH per_user AS (
        SELECT userId, AVG(rating) AS avg_rating
        FROM ratings
        GROUP BY userId
    )
    SELECT
        FLOOR(avg_rating * 2) / 2 AS avg_rating_bucket,
        COUNT(*)                  AS n_users
    FROM per_user
    GROUP BY avg_rating_bucket
    ORDER BY avg_rating_bucket
""").df()

print(avg_rating_per_user.to_string(index=False))


# Q4. Movies with the highest average rating
MIN_RATINGS = 50  # com o 100K; no 32M usa-se 1000

print(f"\n--- Q4: TOP 20 MOVIES BY AVG RATING (>= {MIN_RATINGS} ratings) ---")

top_movies = con.sql(f"""
    SELECT
        m.title,
        COUNT(*)                 AS n_ratings,
        ROUND(AVG(r.rating), 3)  AS avg_rating
    FROM ratings r
    JOIN movies m USING (movieId)
    GROUP BY m.movieId, m.title
    HAVING COUNT(*) >= {MIN_RATINGS}
    ORDER BY avg_rating DESC, n_ratings DESC
    LIMIT 20
""").df()

print(top_movies.to_string(index=False))