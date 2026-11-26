# Research Question 3: How have monster-related movie themes evolved over time?
#
# Step 1: Explore monster-related tags
# =====================================================

from pathlib import Path
import duckdb

# -----------------------------------------------------
# 1. Data paths
# -----------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PARQUET_DIR = PROJECT_ROOT / "Data" / "Parquet" / "ml-32m"

tags_path = PARQUET_DIR / "tags.parquet"

# -----------------------------------------------------
# 2. Explore monster-related tags
# -----------------------------------------------------

query = """
SELECT
    LOWER(tag) AS tag,
    COUNT(*) AS tag_count,
    COUNT(DISTINCT movieId) AS total_movies
FROM read_parquet(?)
WHERE regexp_matches(
    LOWER(tag),
    'zombie|vampire|werewolf|alien|monster|kaiju|dinosaur'
)
GROUP BY LOWER(tag)
ORDER BY tag_count DESC
LIMIT 30
"""

con = duckdb.connect()

df = con.execute(
    query,
    [str(tags_path)]
).df()

con.close()

# -----------------------------------------------------
# 3. Results
# -----------------------------------------------------

print("\n===== MONSTER-RELATED TAGS =====")
print(df.to_string(index=False))
