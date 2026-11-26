# ---
# jupyter:
#   jupytext:
#     cell_metadata_filter: -all
#     formats: notebooks///ipynb,src///py:percent
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
from pathlib import Path
import duckdb


# %% [markdown]
# --------------------------------------------------
# Project paths
# --------------------------------------------------

# %%
PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
    if "__file__" in globals()
    else Path.cwd().resolve().parent  # notebooks run from notebooks/
)
PARQUET_DIR = PROJECT_ROOT / "Data" / "Parquet"

# %%
movies_path = PARQUET_DIR / "movies.parquet"
ratings_path = PARQUET_DIR / "ratings.parquet"
tags_path = PARQUET_DIR / "tags.parquet"
links_path = PARQUET_DIR / "links.parquet"


# %% [markdown]
# --------------------------------------------------
# DuckDB connection
# --------------------------------------------------

# %%
con = duckdb.connect()


# %%
print("Starting data validation and EDA...")

# %% [markdown]
# --------------------------------------------------
# Dataset overview
# --------------------------------------------------

# %%
print("\n--- DATASET OVERVIEW ---")

# %%
datasets = {
    "movies": movies_path,
    "ratings": ratings_path,
    "tags": tags_path,
    "links": links_path
}

# %%
for name, path in datasets.items():

    row_count = con.sql(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{path.as_posix()}')
        """
    ).fetchall()[0][0]

    print(f"{name}: {row_count} rows")


# %% [markdown]
# --------------------------------------------------
# Unique IDs and duplicates
# --------------------------------------------------

# %%
print("\n--- UNIQUE IDS ---")

# %%
movies_summary = con.sql(
    f"""
    SELECT
        COUNT(*) AS total_rows,
        COUNT(DISTINCT movieId) AS unique_movie_ids
    FROM read_parquet('{movies_path.as_posix()}')
    """
).limit(1).fetchall()[0]

# %%
print("Movies:")
print("  Rows:", movies_summary[0])
print("  Unique movie IDs:", movies_summary[1])


# %%
ratings_summary = con.sql(
    f"""
    SELECT
        COUNT(*) AS total_ratings,
        COUNT(DISTINCT userId) AS unique_users,
        COUNT(DISTINCT movieId) AS rated_movies
    FROM read_parquet('{ratings_path.as_posix()}')
    """
).limit(1).fetchall()[0]

# %%
print("\nRatings:")
print("  Ratings:", ratings_summary[0])
print("  Users:", ratings_summary[1])
print("  Rated movies:", ratings_summary[2])

# %% [markdown]
# --------------------------------------------------
# Rating statistics
# --------------------------------------------------

# %%
print("\n--- RATING STATISTICS ---")

# %%
rating_stats = con.sql(
    f"""
    SELECT
        COUNT(*) AS total_ratings,
        MIN(rating) AS min_rating,
        MAX(rating) AS max_rating,
        ROUND(AVG(rating), 2) AS mean_rating,
        MEDIAN(rating) AS median_rating
    FROM read_parquet('{ratings_path.as_posix()}')
    """
).limit(1).fetchall()[0]

# %%
print("Total ratings:", rating_stats[0])
print("Minimum rating:", rating_stats[1])
print("Maximum rating:", rating_stats[2])
print("Mean rating:", rating_stats[3])
print("Median rating:", rating_stats[4])

# %% [markdown]
# --------------------------------------------------
# Rating distribution
# --------------------------------------------------

# %%
print("\n--- RATING DISTRIBUTION ---")

# %%
rating_distribution = con.sql(
    f"""
    SELECT
        rating,
        COUNT(*) AS number_of_ratings
    FROM read_parquet('{ratings_path.as_posix()}')
    GROUP BY rating
    ORDER BY rating
    """
).df()

# %%
print(rating_distribution)

# %% [markdown]
# --------------------------------------------------
# Temporal coverage
# --------------------------------------------------

# %%
print("\n--- TEMPORAL COVERAGE ---")

# %%
temporal_summary = con.sql(
    f"""
    SELECT
        CAST(MIN(TO_TIMESTAMP(timestamp)) AS TIMESTAMP) AS first_rating,
        CAST(MAX(TO_TIMESTAMP(timestamp)) AS TIMESTAMP) AS last_rating,
        MIN(YEAR(TO_TIMESTAMP(timestamp))) AS first_year,
        MAX(YEAR(TO_TIMESTAMP(timestamp))) AS last_year
    FROM read_parquet('{ratings_path.as_posix()}')
    """
).limit(1).fetchall()[0]

# %%
print("First rating:", temporal_summary[0])
print("Last rating:", temporal_summary[1])
print(
    "Rating years:",
    temporal_summary[2],
    "-",
    temporal_summary[3]
)

# %% [markdown]
# --------------------------------------------------
# Ratings by year
# --------------------------------------------------

# %%
print("\n--- RATINGS BY YEAR ---")

# %%
ratings_by_year = con.sql(
    f"""
    SELECT
        YEAR(TO_TIMESTAMP(timestamp)) AS rating_year,
        COUNT(*) AS number_of_ratings
    FROM read_parquet('{ratings_path.as_posix()}')
    GROUP BY rating_year
    ORDER BY rating_year
    """
).df()

# %%
print(ratings_by_year)
