# ---
# jupyter:
#   jupytext:
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

# %% [markdown]
# # Q: Genre Evolution & Audience Shifts
# - Genre fatigue vs. resurgence: How have average ratings and total viewing volume for genres like Westerns, Sci-Fi, or Superheroes changed from the late 1990s to today?
# - Cross-genre performance: Do hybrid films (e.g., Comedy|Sci-Fi or Horror|Mystery) earn higher average ratings than single-genre films, or do they polarize viewers?
# - The "Sequel Decay" effect: Using movie titles and release years, how sharply does audience sentiment drop between an original movie and its sequels?

# %%
import sys
from pathlib import Path

# %%
PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
    if "__file__" in globals()
    else Path.cwd().resolve().parent  # notebooks run from notebooks/
)

sys.path.insert(0, str(PROJECT_ROOT / "src"))

RAW_DIR = PROJECT_ROOT / "Data" / "Raw"
PARQUET_DIR = PROJECT_ROOT / "Data" / "Parquet"

# %%
IMDB_RAW = RAW_DIR / "IMDB"
IMDB_RAW.mkdir(parents=True, exist_ok=True)

IMDB_PARQUET = PARQUET_DIR / "IMDB"
IMDB_PARQUET.mkdir(parents=True, exist_ok=True)

# %%
