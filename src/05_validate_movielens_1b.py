
from pathlib import Path
import time
import statistics

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import duckdb

# =====================================================
# Performance & Scalability Benchmark
#
# Objective:
# Convert 1.224B interactions to Parquet and compare local DuckDB performance with AWS Athena.
# =====================================================

RAW = Path(r"C:\BDF_Data\Raw\ml-1b\ml-20mx16x32")
OUTPUT = Path(r"C:\BDF_Data\Parquet\ml-1b")
OUTPUT.mkdir(parents=True, exist_ok=True)

EXPECTED_ROWS = 1_223_962_043
BATCH_SIZE = 500_000
REPETITIONS = 5

schema = pa.schema([
    ("userId", pa.int64()),
    ("itemId", pa.int64())
])

# =====================================================
# STEP 1 - NPZ TO PARQUET
# Process one training file at a time.
# =====================================================

npz_files = sorted(RAW.glob("trainx16x32_*.npz"))

assert len(npz_files) == 16, "Missing training files"

for file in npz_files:

    destination = OUTPUT / f"{file.stem}.parquet"

    # Reuse previously converted files
    if destination.exists():
        print(f"Already exists: {destination.name}")
        continue

    start_time = time.perf_counter()

    with np.load(file, allow_pickle=False) as data:
        array = data["arr_0"]

    # Write in batches
    with pq.ParquetWriter(
        destination,
        schema=schema,
        compression="zstd"
    ) as writer:

        for start in range(0, len(array), BATCH_SIZE):

            batch = array[start:start + BATCH_SIZE]

            table = pa.table({
                "userId": batch[:, 0],
                "itemId": batch[:, 1]
            }, schema=schema)

            writer.write_table(table)

    elapsed = time.perf_counter() - start_time

    print(
        f"Converted {file.name}: "
        f"{len(array):,} rows in {elapsed:.2f}s"
    )

    del array

# =====================================================
# STEP 2 - VALIDATE PARQUET DATASET
# =====================================================

parquet_files = sorted(
    OUTPUT.glob("trainx16x32_*.parquet")
)

assert len(parquet_files) == 16, "Missing Parquet files"

total_rows = sum(
    pq.read_metadata(file).num_rows
    for file in parquet_files
)

print(f"\nTotal rows: {total_rows:,}")

assert total_rows == EXPECTED_ROWS, "Row count mismatch"

# =====================================================
# STEP 3 - FULL DATASET DUCKDB BENCHMARK
# =====================================================

pattern = str(
    OUTPUT / "trainx16x32_*.parquet"
).replace("\\", "/")

query = """
SELECT
    itemId,
    COUNT(*) AS interactions
FROM read_parquet(?)
GROUP BY itemId
ORDER BY interactions DESC, itemId
LIMIT 10
"""

times = []

with duckdb.connect() as con:

    con.execute("SET threads = 4")
    con.execute(
        "SET temp_directory = 'C:/BDF_Data/duckdb_temp'"
    )

    # Warm-up, not included in measurements
    con.execute(query, [pattern]).fetchall()

    for i in range(REPETITIONS):

        start = time.perf_counter()

        result = con.execute(
            query, [pattern]
        ).fetchall()

        elapsed = time.perf_counter() - start
        times.append(elapsed)

        print(f"Run {i + 1}: {elapsed:.3f}s")

# =====================================================
# STEP 4 - RESULTS
# =====================================================

print("\n===== FINAL BENCHMARK =====")
print("Engine: DuckDB")
print("Format: Parquet + ZSTD")
print(f"Total interactions: {total_rows:,}")
print(f"Median: {statistics.median(times):.3f}s")

print("\nTop 10 items:")
for item_id, count in result:
    print(f"Item {item_id}: {count:,}")
