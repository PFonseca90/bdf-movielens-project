# =====================================================
# Research Question 2: How do movie releases and audience ratings 
# evolve across genres and release years?
# =====================================================

from pathlib import Path
import duckdb
import matplotlib.pyplot as plt

# -----------------------------------------------------
# 1. Data paths and genre selection
# -----------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARQUET_DIR = PROJECT_ROOT / "Data" / "Parquet" / "ml-32m"

movies_path = PARQUET_DIR / "movies.parquet"
ratings_path = PARQUET_DIR / "ratings.parquet"

# Only affects line charts, not the analysis
selected_genres = [
    "Action",
    "Animation",
    "Comedy",
    "Horror",
    "Musical",
    "Sci-Fi",
    "Western"
]

# -----------------------------------------------------
# 2. Annual analysis with DuckDB
# -----------------------------------------------------

query = """
WITH movies AS (
    SELECT
        movieId,
        TRY_CAST(
            regexp_extract(title, '[(]([0-9]{4})[)]', 1)
            AS INTEGER
        ) AS release_year,
        genres
    FROM read_parquet(?)
),

ratings AS (
    SELECT
        movieId,
        COUNT(*) AS rating_count,
        SUM(rating) AS rating_sum
    FROM read_parquet(?)
    GROUP BY movieId
),

movies_by_genre AS (
    SELECT
        movieId,
        release_year,
        UNNEST(string_split(genres, '|')) AS genre
    FROM movies
    WHERE release_year BETWEEN 1950 AND 2023
),

year_totals AS (
    SELECT
        release_year,
        COUNT(*) AS movies_in_year
    FROM movies
    WHERE release_year BETWEEN 1950 AND 2023
    GROUP BY release_year
)

SELECT
    m.release_year,
    m.genre,
    COUNT(*) AS total_movies,
    MAX(y.movies_in_year) AS movies_in_year,
    SUM(COALESCE(r.rating_count, 0)) AS total_ratings,
    SUM(COALESCE(r.rating_sum, 0)) AS rating_sum

FROM movies_by_genre m

LEFT JOIN ratings r
    ON m.movieId = r.movieId

JOIN year_totals y
    ON m.release_year = y.release_year

WHERE m.genre <> '(no genres listed)'

GROUP BY m.release_year, m.genre
ORDER BY m.release_year, m.genre
"""

con = duckdb.connect()

df = con.execute(
    query,
    [str(movies_path), str(ratings_path)]
).df()

con.close()

# Annual indicators
df["genre_share_pct"] = (
    df["total_movies"] / df["movies_in_year"] * 100
)

df["avg_rating"] = (
    df["rating_sum"] / df["total_ratings"]
).round(2)

# -----------------------------------------------------
# 3. Annual results - All years and genres
# -----------------------------------------------------

print("\n===== GENRE EVOLUTION - ANNUAL =====")
print("Genres analysed:", df["genre"].nunique())
print("Years analysed:", df["release_year"].nunique())

columns = [
    "release_year",
    "genre",
    "total_movies",
    "genre_share_pct",
    "total_ratings",
    "avg_rating"
]

print(df[columns].round(2).to_string(index=False))

# -----------------------------------------------------
# 4. Aggregate annual data by decade
# -----------------------------------------------------

df["decade"] = (df["release_year"] // 10) * 10

decade_df = df.groupby(
    ["decade", "genre"], as_index=False
)[
    ["total_movies", "total_ratings", "rating_sum"]
].sum()

# Count all movies in each decade only once
decade_totals = (
    df[["release_year", "decade", "movies_in_year"]]
    .drop_duplicates(subset="release_year")
    .groupby("decade")["movies_in_year"]
    .sum()
)

decade_df["genre_share_pct"] = (
    decade_df["total_movies"] /
    decade_df["decade"].map(decade_totals) * 100
)

# Weighted average of all ratings in the decade
decade_df["avg_rating"] = (
    decade_df["rating_sum"] /
    decade_df["total_ratings"].replace(0, float("nan"))
)

print("\n===== GENRE EVOLUTION - BY DECADE =====")

print(
    decade_df[
        ["decade", "genre", "total_movies",
         "genre_share_pct", "total_ratings", "avg_rating"]
    ].round(2).to_string(index=False)
)

# -----------------------------------------------------
# 5. Prepare line charts
# -----------------------------------------------------

df_plot = decade_df[
    decade_df["genre"].isin(selected_genres)
]

movies = df_plot.pivot(
    index="decade",
    columns="genre",
    values="total_movies"
)

share = df_plot.pivot(
    index="decade",
    columns="genre",
    values="genre_share_pct"
)

ratings = df_plot.pivot(
    index="decade",
    columns="genre",
    values="avg_rating"
)

# -----------------------------------------------------
# 6. Three line charts by decade
# -----------------------------------------------------

fig, axes = plt.subplots(
    3, 1, figsize=(12, 12), sharex=True
)

movies.plot(ax=axes[0], marker="o")
axes[0].set_title("Number of Movies by Release Decade")
axes[0].set_ylabel("Number of Movies")
axes[0].grid(alpha=0.3)

share.plot(ax=axes[1], marker="o")
axes[1].set_title("Genre Share by Release Decade")
axes[1].set_ylabel("Share (%)")
axes[1].grid(alpha=0.3)

ratings.plot(ax=axes[2], marker="o")
axes[2].set_title("Average Audience Rating by Release Decade")
axes[2].set_ylabel("Average Rating")
axes[2].set_xlabel("Release Decade")
axes[2].set_ylim(0.5, 5)
axes[2].grid(alpha=0.3)

plt.tight_layout()
plt.show()