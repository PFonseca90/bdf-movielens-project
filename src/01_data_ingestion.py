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

# %%
# Project paths use (__file__ ).resolve().parent.parent in order to run the code in any machine without changinf the path.
PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
    if "__file__" in globals()
    else Path.cwd().resolve().parent  # notebooks run from notebooks/
)
print(PROJECT_ROOT)

# %%
RAW_DIR = PROJECT_ROOT / "Data" / "Raw"
PARQUET_DIR = PROJECT_ROOT / "Data" / "Parquet"

# %%
# MovieLens files
FILES = [
    "movies.csv",
    "ratings.csv",
    "tags.csv",
    "links.csv",
]

# %%
print("Project root:", PROJECT_ROOT)
print("Raw data folder:", RAW_DIR)
print("Parquet folder:", PARQUET_DIR)

# %%
# Check if folders exist
print("\nFolder validation")

# %%
print("Raw folder exists:", RAW_DIR.exists())

# %%
PARQUET_DIR.mkdir(parents=True, exist_ok=True)

# %%
print("Parquet folder exists:", PARQUET_DIR.exists())

# %% [markdown]
# check if files exist

# %%
print("\nMovieLens files")

# %%
for file_name in FILES:
    file_path = RAW_DIR / file_name

    if file_path.exists():
        print(f"[OK] {file_name}")
    else:
        print(f"[MISSING] {file_name}")

# %% [markdown]
# --------------------------------------------------
# Inspect CSV files with DuckDB
# --------------------------------------------------

# %%
print("\nDataset inspection")

# %%
for file_name in FILES:
    file_path = RAW_DIR / file_name

    print(f"\n--- {file_name} ---")

    # Count rows
    row_count = duckdb.sql(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{file_path.as_posix()}') /* as_posix() is used to convert the path to a string that can be used in SQL queries */
        """
    ).fetchall()[0][0]

    print("Rows:", row_count)

    # Inspect columns and inferred data types
    schema = duckdb.sql(
        f"""
        DESCRIBE
        SELECT *
        FROM read_csv_auto('{file_path.as_posix()}')
        """
    ).fetchall()

    print("Columns:")

    for column in schema:
        print(f"  {column[0]} -> {column[1]}")

# %% [markdown]
# --------------------------------------------------
# Convert CSV files to Parquet
# --------------------------------------------------

# %%
print("\nCSV -> Parquet conversion")

# %%
for file_name in FILES:
    csv_path = RAW_DIR / file_name

    parquet_name = file_name.replace(".csv", ".parquet")
    parquet_path = PARQUET_DIR / parquet_name

    duckdb.sql(
        f"""
        COPY (
            SELECT *
            FROM read_csv_auto('{csv_path.as_posix()}')
        )
        TO '{parquet_path.as_posix()}'
        (
            FORMAT PARQUET,
            COMPRESSION ZSTD
        )
        """
    )

    print(f"[CREATED] {parquet_name}")

# %% [markdown]
# --------------------------------------------------
# Validate Parquet files
# --------------------------------------------------

# %%
print("\nParquet validation")

# %%
for file_name in FILES:
    csv_path = RAW_DIR / file_name

    parquet_name = file_name.replace(".csv", ".parquet")
    parquet_path = PARQUET_DIR / parquet_name

    csv_rows = duckdb.sql(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv_path.as_posix()}')
        """
    ).fetchall()[0][0]

    parquet_rows = duckdb.sql(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{parquet_path.as_posix()}')
        """
    ).fetchall()[0][0]

    if csv_rows == parquet_rows:
        print(f"[OK] {parquet_name}: {parquet_rows} rows")
    else:
        print(
            f"[ERROR] {parquet_name}: "
            f"CSV={csv_rows}, Parquet={parquet_rows}"
        )
