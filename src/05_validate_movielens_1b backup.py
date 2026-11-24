
from pathlib import Path
import zipfile
import numpy as np

DATA_DIR = Path(
    r"C:\BDF_Data\Raw\ml-1b\ml-20mx16x32"
)

# =====================================================
# EXPERIMENT 1 - DATASET INVENTORY
#
# Objective:
# Count train/test interactions without loading the complete arrays into RAM.
# =====================================================

train_total = 0
test_total = 0

files = sorted(DATA_DIR.glob("*.npz"))

for file in files:

    with zipfile.ZipFile(file) as archive:
        with archive.open("arr_0.npy") as member:

            # Identify the NPY file version
            version = np.lib.format.read_magic(member)

            # Read the array header while the file is open
            if version == (1, 0):
                shape, _, _ = (
                    np.lib.format.read_array_header_1_0(member)
                )
            elif version == (2, 0):
                shape, _, _ = (
                    np.lib.format.read_array_header_2_0(member)
                )
            else:
                raise ValueError(
                    f"Unsupported NPY version: {version}"
                )

    rows = shape[0]

    if file.name.startswith("train"):
        train_total += rows

    elif file.name.startswith("test"):
        test_total += rows

    print(f"{file.name}: {rows:,} interactions")

print("\n===== DATASET SUMMARY =====")
print("Files:", len(files))
print("Train interactions:", f"{train_total:,}")
print("Test interactions:", f"{test_total:,}")
print("Total interactions:", f"{train_total + test_total:,}")


# =====================================================
# EXPERIMENT 2 - NPZ TO PARQUET BENCHMARK
#
# Objective: Convert one MovieLens 1B training shard to Parquet and measure conversion time and storage efficiency.
# =====================================================

import time
import pyarrow as pa
import pyarrow.parquet as pq

INPUT_FILE = DATA_DIR / "trainx16x32_9.npz"

OUTPUT_DIR = Path(r"C:\BDF_Data\Parquet\ml-1b")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_FILE = OUTPUT_DIR / "trainx16x32_9.parquet"

BATCH_SIZE = 500_000

start_time = time.perf_counter()

# Load a single NPZ shard into memory
with np.load(INPUT_FILE, allow_pickle=False) as data:
    interactions = data["arr_0"]

# Convert to Parquet in batches
schema = pa.schema([
    ("userId", pa.int64()),
    ("itemId", pa.int64())
])

with pq.ParquetWriter(
    OUTPUT_FILE,
    schema=schema,
    compression="zstd"
) as writer:

    for start in range(0, len(interactions), BATCH_SIZE):
        end = min(start + BATCH_SIZE, len(interactions))
        batch = interactions[start:end]

        table = pa.Table.from_arrays(
            [
                pa.array(batch[:, 0]),
                pa.array(batch[:, 1])
            ],
            schema=schema
        )

        writer.write_table(table)

elapsed = time.perf_counter() - start_time

# Validate output without reading every row
parquet_metadata = pq.read_metadata(OUTPUT_FILE)

input_mb = INPUT_FILE.stat().st_size / (1024 ** 2)
output_mb = OUTPUT_FILE.stat().st_size / (1024 ** 2)

print("\n===== EXPERIMENT 2 RESULTS =====")
print("Input interactions:", f"{len(interactions):,}")
print("Parquet interactions:", f"{parquet_metadata.num_rows:,}")
print("Conversion time:", f"{elapsed:.2f} seconds")
print("NPZ size:", f"{input_mb:.2f} MiB")
print("Parquet size:", f"{output_mb:.2f} MiB")
print(
    "Storage difference:",
    f"{(1 - output_mb / input_mb) * 100:.2f}%"
)

del interactions



# =====================================================
# EXPERIMENT 2B - REPEATED QUERY BENCHMARK
#
# Objective:
# Compare NumPy/NPZ and DuckDB/Parquet using 5 repetitions and median execution times.
# =====================================================

import duckdb
import statistics
import gc

REPETITIONS = 5

numpy_times = []
duckdb_times = []

con = duckdb.connect()

for i in range(REPETITIONS):

    # NumPy: file loading + aggregation
    start = time.perf_counter()

    with np.load(INPUT_FILE, allow_pickle=False) as data:
        arr = data["arr_0"]

    np_count = len(arr)
    np_users = len(np.unique(arr[:, 0]))

    numpy_times.append(time.perf_counter() - start)

    del arr
    gc.collect()

    # DuckDB: Parquet query
    start = time.perf_counter()

    result = con.execute(
        """
        SELECT
            COUNT(*) AS interactions,
            COUNT(DISTINCT userId) AS users
        FROM read_parquet(?)
        """,
        [str(OUTPUT_FILE)]
    ).fetchone()

    duckdb_times.append(time.perf_counter() - start)

    assert np_count == result[0]
    assert np_users == result[1]

    print(
        f"Run {i + 1}: "
        f"NumPy={numpy_times[-1]:.3f}s | "
        f"DuckDB={duckdb_times[-1]:.3f}s"
    )

con.close()

numpy_median = statistics.median(numpy_times)
duckdb_median = statistics.median(duckdb_times)

print("\n===== REPEATED BENCHMARK =====")
print(f"NumPy median: {numpy_median:.3f}s")
print(f"DuckDB median: {duckdb_median:.3f}s")
print(f"Speed ratio: {numpy_median / duckdb_median:.2f}x")


# =====================================================
# EXPERIMENT 3 - FULL DATASET CONTENT INSPECTION
#
# Objective: Inspect all 32 NPZ files, one at a time.
#
# Checks:
# - Array shape and data type
# - User/item identifier ranges
# - Negative identifiers
# - Sorting and consecutive duplicates
# - Sample interactions
# =====================================================

import gc

validation_results = []

for file in files:

    print(f"\nInspecting: {file.name}", flush=True)

    with np.load(file, allow_pickle=False) as data:
        if data.files != ["arr_0"]:
            raise ValueError(
                f"Unexpected arrays in {file.name}: {data.files}"
            )

        array = data["arr_0"]

    if array.ndim != 2 or array.shape[1] != 2:
        raise ValueError(f"Unexpected shape: {array.shape}")

    # Global ranges for this file
    min_user = int(array[:, 0].min())
    max_user = int(array[:, 0].max())
    min_item = int(array[:, 1].min())
    max_item = int(array[:, 1].max())

    # Identifier validation
    negative_users = int(np.count_nonzero(array[:, 0] < 0))
    negative_items = int(np.count_nonzero(array[:, 1] < 0))

    # Check lexicographic ordering
    users_sorted = bool(
        np.all(array[1:, 0] >= array[:-1, 0])
    )

    same_user = array[1:, 0] == array[:-1, 0]

    items_sorted = bool(
        np.all(
            (array[1:, 1] >= array[:-1, 1]) | ~same_user
        )
    )

    # Consecutive duplicates are exhaustive only when sorting is confirmed.
    duplicates = None

    if users_sorted and items_sorted:
        same_item = array[1:, 1] == array[:-1, 1]
        duplicates = int(
            np.count_nonzero(same_user & same_item)
        )

    result = {
        "file": file.name,
        "split": "train" if file.name.startswith("train") else "test",
        "rows": len(array),
        "dtype": str(array.dtype),
        "min_user": min_user,
        "max_user": max_user,
        "min_item": min_item,
        "max_item": max_item,
        "negative_users": negative_users,
        "negative_items": negative_items,
        "users_sorted": users_sorted,
        "items_sorted": items_sorted,
        "duplicates": duplicates,
    }

    validation_results.append(result)

    print("Rows:", f"{result['rows']:,}")
    print("User range:", min_user, "-", max_user)
    print("Item range:", min_item, "-", max_item)
    print("Sorted:", users_sorted, items_sorted)
    print("Duplicates:", duplicates)
    print("First 3 interactions:", array[:3].tolist())

    del array, same_user
    gc.collect()

print("\n===== FULL DATASET VALIDATION SUMMARY =====")

print("Files inspected:", len(validation_results))

print(
    "Total interactions:",
    f"{sum(r['rows'] for r in validation_results):,}"
)

print(
    "Files with negative IDs:",
    sum(
        1 for r in validation_results
        if r["negative_users"] > 0
        or r["negative_items"] > 0
    )
)

print(
    "Files with invalid sorting:",
    sum(
        1 for r in validation_results
        if not r["users_sorted"]
        or not r["items_sorted"]
    )
)

print(
    "Files with confirmed duplicates:",
    sum(
        1 for r in validation_results
        if r["duplicates"] is not None
        and r["duplicates"] > 0
    )
)


# =====================================================
# EXPERIMENT 4 - USER INTERACTION DISTRIBUTION
#
# Objective:
# Understand how many interactions each user has across the complete MovieLens 1B dataset.
# =====================================================

user_counts = []

for file in files:
    if not file.name.startswith("train"):
        continue

    print(f"Analyzing users: {file.name}", flush=True)

    with np.load(file, allow_pickle=False) as data:
        array = data["arr_0"]

    # Count interactions for each user
    users, counts = np.unique(
        array[:, 0],
        return_counts=True
    )

    user_counts.append(counts)

    del array, users, counts

all_user_counts = np.concatenate(user_counts)

print("\n===== USER INTERACTION DISTRIBUTION =====")
print("Users:", f"{len(all_user_counts):,}")
print("Mean:", round(np.mean(all_user_counts), 2))
print("Median:", np.median(all_user_counts))
print("Minimum:", np.min(all_user_counts))
print("Maximum:", np.max(all_user_counts))
print("P90:", np.percentile(all_user_counts, 90))
print("P99:", np.percentile(all_user_counts, 99))


# =====================================================
# EXPERIMENT 5 - ITEM POPULARITY ANALYSIS
#
# Objective:
# Identify the most popular synthetic items across all MovieLens 1B training files.
#
# Metrics:
# - Total interactions per item
# - Top 10 most popular items
# - Popularity concentration (Top 1%)
# =====================================================

ITEM_COUNT = 855_776

# Initialize one counter per synthetic item
item_counts = np.zeros(ITEM_COUNT, dtype=np.int64)

for file in files:
    if not file.name.startswith("train"):
        continue

    print(f"Analyzing items: {file.name}", flush=True)

    with np.load(file, allow_pickle=False) as data:
        array = data["arr_0"]

    # Count item occurrences in the current file
    counts = np.bincount(
        array[:, 1],
        minlength=ITEM_COUNT
    )

    # Add counts to the global total
    item_counts += counts

    del array, counts

# Rank items by interaction volume
top_items = np.argsort(item_counts)[::-1]

print("\n===== TOP 10 MOST POPULAR ITEMS =====")

for rank, item_id in enumerate(top_items[:10], start=1):
    print(
        f"{rank}. Item {item_id}: "
        f"{item_counts[item_id]:,} interactions"
    )

# Count items with at least one interaction
active_items = np.count_nonzero(item_counts)

# Calculate top 1% popularity concentration
top_1_count = int(np.ceil(active_items * 0.01))

sorted_active_counts = np.sort(
    item_counts[item_counts > 0]
)[::-1]

top_1_interactions = np.sum(
    sorted_active_counts[:top_1_count]
)

total_interactions = np.sum(item_counts)

concentration = (
    100 * top_1_interactions / total_interactions
)

print("\n===== ITEM POPULARITY SUMMARY =====")
print("Active items:", f"{active_items:,}")
print("Top 1% items:", f"{top_1_count:,}")
print("Total interactions:", f"{total_interactions:,}")
print(
    "Top 1% interactions:",
    f"{top_1_interactions:,}"
)
print(
    "Popularity concentration:",
    f"{concentration:.2f}%"
)