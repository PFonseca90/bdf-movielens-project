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
from time import perf_counter
from statistics import median
import gc
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

# %%
CSV_PATH = PROJECT_ROOT / "Data" / "Raw" / "ml-32m" / "ratings.csv"
PARQUET_PATH = PROJECT_ROOT / "Data" / "Parquet" / "ml-32m" / "ratings.parquet"

# %% [markdown]
# --------------------------------------------------
# DuckDB connection
# --------------------------------------------------

# %%
con = duckdb.connect()

# %% [markdown]
# --------------------------------------------------
# Queries
# --------------------------------------------------

# %%
queries = {
    "CSV": f"""
        SELECT
            COUNT(*) AS total_ratings,
            ROUND(AVG(rating), 2) AS avg_rating
        FROM read_csv_auto('{CSV_PATH.as_posix()}')
    """,

    "Parquet": f"""
        SELECT
            COUNT(*) AS total_ratings,
            ROUND(AVG(rating), 2) AS avg_rating
        FROM read_parquet('{PARQUET_PATH.as_posix()}')
    """
}

# %% [markdown]
# --------------------------------------------------
# Performance Benchmark - CSV vs Parquet
# --------------------------------------------------

# %%
print("\n--- CSV VS PARQUET BENCHMARK ---")

# %%
# File sizes
csv_size = CSV_PATH.stat().st_size / (1024 ** 2)
parquet_size = PARQUET_PATH.stat().st_size / (1024 ** 2)

# %%
compression = (1 - parquet_size / csv_size) * 100

# %%
print(f"\nCSV size: {csv_size:.2f} MB")
print(f"Parquet size: {parquet_size:.2f} MB")
print(f"Size reduction: {compression:.2f}%")

print(1+2)

# %%
# Repeat queries
n_runs = 5
times = {"CSV": [], "Parquet": []}

# %%
for run in range(n_runs):

    print(f"\n--- RUN {run + 1} ---")

    # Alternate query order
    formats = (
        ["CSV", "Parquet"]
        if run % 2 == 0
        else ["Parquet", "CSV"]
    )

    for file_format in formats:

        gc.collect()

        start_time = perf_counter()

        result = con.execute(
            queries[file_format]
        ).fetchone()

        execution_time = perf_counter() - start_time

        times[file_format].append(execution_time)

        print(
            f"{file_format}: {execution_time:.4f} seconds"
        )

        assert result[0] == 32000204
        assert result[1] == 3.54

# %%
# Summary
csv_median = median(times["CSV"])
parquet_median = median(times["Parquet"])

# %%
print("\n--- BENCHMARK SUMMARY ---")

# %%
print(f"CSV median: {csv_median:.4f} seconds")
print(f"Parquet median: {parquet_median:.4f} seconds")

# %%
print(
    f"Speedup: {csv_median / parquet_median:.2f}x"
)
