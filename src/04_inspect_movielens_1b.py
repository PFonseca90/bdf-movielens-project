
from pathlib import Path
import numpy as np

# MovieLens 1B - Inspect a single NPZ shard
file_path = Path(
    r"C:\BDF_Data\Raw\ml-1b\ml-20mx16x32\trainx16x32_1.npz"
)

with np.load(file_path, allow_pickle=False) as data:
    array = data["arr_0"]

    print("Shape:", array.shape)
    print("Data type:", array.dtype)

    # Display the first five interactions
    print("\nFirst 5 rows:")
    print(array[:5])

    # Inspect a small sample without processing
    # the entire dataset again
    sample = array[:10000]

    print("\nFirst column:")
    print("Min:", sample[:, 0].min())
    print("Max:", sample[:, 0].max())

    print("\nSecond column:")
    print("Min:", sample[:, 1].min())
    print("Max:", sample[:, 1].max())
    
# Data Quality - MovieLens 1B
print("\nDATA QUALITY CHECK")

print("Total interactions:", len(array))

print("Negative user IDs:", np.sum(array[:, 0] < 0))
print("Negative item IDs:", np.sum(array[:, 1] < 0))

print("Users in sample:", len(np.unique(array[:10000, 0])))
print("Items in sample:", len(np.unique(array[:10000, 1])))

# =====================================================
# DATA QUALITY CHECK 2 - Duplicate interactions
# =====================================================

# Sample use to avoid processing all 112M rows
sample = array[:100_000]

# Count unique user-item pairs
unique_pairs = np.unique(sample, axis=0)

# Calculate duplicate interactions
duplicate_count = len(sample) - len(unique_pairs)

print("\nDUPLICATE INTERACTIONS")
print("Sample size:", len(sample))
print("Unique interactions:", len(unique_pairs))
print("Duplicate interactions:", duplicate_count)
print(
    "Duplicate percentage:",
    round(100 * duplicate_count / len(sample), 2),
    "%"
)

# =====================================================
# DATA STRUCTURE CHECK - Sorting
# =====================================================

# Check if user IDs never decrease
users_sorted = np.all(
    array[1:, 0] >= array[:-1, 0]
)

# Check if item IDs increase within each user
same_user = array[1:, 0] == array[:-1, 0]

items_sorted = np.all(
    (array[1:, 1] >= array[:-1, 1]) | ~same_user
)

print("\nSORTING VALIDATION")
print("Users sorted:", users_sorted)
print("Items sorted within users:", items_sorted)


# =====================================================
# DATA QUALITY CHECK 3 - Full duplicate validation
# =====================================================

# Compare consecutive user IDs
same_user = array[1:, 0] == array[:-1, 0]

# Compare consecutive item IDs
same_item = array[1:, 1] == array[:-1, 1]

# A duplicate exists when both IDs are identical
duplicates = np.count_nonzero(same_user & same_item)

print("\nFULL FILE DUPLICATE VALIDATION")
print("Total interactions:", len(array))
print("Duplicate interactions:", duplicates)
print(
    "Duplicate percentage:",
    round(100 * duplicates / len(array), 6),
    "%"
)
