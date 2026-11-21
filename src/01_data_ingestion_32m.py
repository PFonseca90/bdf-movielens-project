from pathlib import Path
import duckdb

# Project paths use (__file__ ).resolve().parent.parent in order to run the code in any machine without changinf the path.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DIR = PROJECT_ROOT / "Data" / "Raw" / "ml-32m"
PARQUET_DIR = PROJECT_ROOT / "Data" / "Parquet" / "ml-32m"

# MovieLens files
FILES = [
    "movies.csv",
    "ratings.csv",
    "tags.csv",
    "links.csv",
]

print("Project root:", PROJECT_ROOT)
print("Raw data folder:", RAW_DIR)
print("Parquet folder:", PARQUET_DIR)

# Check if folders exist
print("\nFolder validation")

print("Raw folder exists:", RAW_DIR.exists())

PARQUET_DIR.mkdir(parents=True, exist_ok=True)

print("Parquet folder exists:", PARQUET_DIR.exists())

# check if files exist

print("\nMovieLens files")

for file_name in FILES:
    file_path = RAW_DIR / file_name

    if file_path.exists():
        print(f"[OK] {file_name}")
    else:
        print(f"[MISSING] {file_name}")
        
# --------------------------------------------------
# Inspect CSV files with DuckDB
# --------------------------------------------------

print("\nDataset inspection")

for file_name in FILES:
    file_path = RAW_DIR / file_name

    print(f"\n--- {file_name} ---")

    # Count rows
    row_count = duckdb.sql(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{file_path.as_posix()}') /* as_posix() is used to convert the path to a string that can be used in SQL queries */
        """
    ).fetchone()[0]

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

# --------------------------------------------------
# Convert CSV files to Parquet
# --------------------------------------------------

print("\nCSV -> Parquet conversion")

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

# --------------------------------------------------
# Validate Parquet files
# --------------------------------------------------

print("\nParquet validation")

for file_name in FILES:
    csv_path = RAW_DIR / file_name

    parquet_name = file_name.replace(".csv", ".parquet")
    parquet_path = PARQUET_DIR / parquet_name

    csv_rows = duckdb.sql(
        f"""
        SELECT COUNT(*)
        FROM read_csv_auto('{csv_path.as_posix()}')
        """
    ).fetchone()[0]

    parquet_rows = duckdb.sql(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{parquet_path.as_posix()}')
        """
    ).fetchone()[0]

    if csv_rows == parquet_rows:
        print(f"[OK] {parquet_name}: {parquet_rows} rows")
    else:
        print(
            f"[ERROR] {parquet_name}: "
            f"CSV={csv_rows}, Parquet={parquet_rows}"
        )

