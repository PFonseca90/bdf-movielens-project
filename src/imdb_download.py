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

# %%
import sys
from pathlib import Path

import duckdb

# %%
PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
    if "__file__" in globals()
    else Path.cwd().resolve().parent  # notebooks run from notebooks/
)

sys.path.insert(0, str(PROJECT_ROOT / "src"))
from common import download_file  # noqa: E402

RAW_DIR = PROJECT_ROOT / "Data" / "Raw"
PARQUET_DIR = PROJECT_ROOT / "Data" / "Parquet"

# %%
IMDB_RAW = RAW_DIR / "IMDB"
IMDB_RAW.mkdir(parents=True, exist_ok=True)

IMDB_PARQUET = PARQUET_DIR / "IMDB"
IMDB_PARQUET.mkdir(parents=True, exist_ok=True)

# %%
imdb_files = [
    "https://datasets.imdbws.com/name.basics.tsv.gz",
    "https://datasets.imdbws.com/title.akas.tsv.gz",
    "https://datasets.imdbws.com/title.basics.tsv.gz",
    "https://datasets.imdbws.com/title.crew.tsv.gz",
    "https://datasets.imdbws.com/title.episode.tsv.gz",
    "https://datasets.imdbws.com/title.principals.tsv.gz",
    "https://datasets.imdbws.com/title.ratings.tsv.gz",
]


# %%
for url in imdb_files:
    download_file(url, IMDB_RAW)

print("downloads completed successfully.")


# %%
def gz_to_parquet(
    gz_path: Path, dest_dir: Path, con: duckdb.DuckDBPyConnection
) -> Path:
    """Decompress an IMDB `.tsv.gz` and write it as a snappy Parquet file.

    DuckDB decompresses the gzip stream on the fly, so no intermediate `.tsv`
    is written to disk. Skips files that already exist.
    """
    dest = dest_dir / gz_path.name.removesuffix(".tsv.gz").replace(".", "_")
    dest = dest.with_suffix(".parquet")
    if dest.exists():
        print(f"skip   {dest.name} (already converted)")
        return dest

    tmp = dest.with_suffix(".parquet.part")
    print(f"convert {gz_path.name} -> {dest.name}")
    con.execute(
        f"""
        COPY (
            SELECT * FROM read_csv(
                '{gz_path}',
                delim = '\t',
                header = true,
                quote = '',        -- IMDb has unescaped quotes inside fields
                escape = '',
                nullstr = '\\N',   -- IMDb's NULL marker
                sample_size = -1   -- scan everything when inferring types
            )
        ) TO '{tmp}' (FORMAT parquet, COMPRESSION snappy)
        """
    )
    tmp.replace(dest)
    print(f"saved  {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest


# %%
con = duckdb.connect()
for gz_file in sorted(IMDB_RAW.glob("*.tsv.gz")):
    gz_to_parquet(gz_file, IMDB_PARQUET, con)
con.close()

print("parquet conversion completed successfully.")


# %%
