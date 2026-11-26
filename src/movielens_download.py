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
import shutil
import sys
import zipfile
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
MOVIELENS_RAW = RAW_DIR / "MovieLens"
MOVIELENS_RAW.mkdir(parents=True, exist_ok=True)

MOVIELENS_PARQUET = PARQUET_DIR / "MovieLens"
MOVIELENS_PARQUET.mkdir(parents=True, exist_ok=True)

# %%
MOVIELENS_URL = "https://files.grouplens.org/datasets/movielens/ml-32m.zip"


# %%
def download_and_extract(url: str, dest_dir: Path, chunk_size: int = 1024 * 1024) -> list[Path]:
    """Download the zip at `url` and extract its files directly into `dest_dir`.

    The archive's top-level folder (e.g. `ml-32m/`) is stripped, so files land
    as `dest_dir/ratings.csv` etc. The zip is deleted afterwards. Skips
    everything if the files are already extracted.
    """
    existing = sorted(p for p in dest_dir.glob("*.csv"))
    if existing:
        print(f"skip   {url.rsplit('/', 1)[-1]} (already extracted)")
        return existing

    zip_path = download_file(url, dest_dir)
    extracted = []
    try:
        with zipfile.ZipFile(zip_path) as zf:
            for member in zf.infolist():
                if member.is_dir():
                    continue
                # keep only the file name: drops the top-level folder, blocks path traversal
                target = dest_dir / Path(member.filename).name
                with zf.open(member) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out, chunk_size)
                extracted.append(target)
                print(f"saved  {target} ({target.stat().st_size / 1e6:.1f} MB)")
    finally:
        zip_path.unlink(missing_ok=True)
    return sorted(extracted)


# %%
download_and_extract(MOVIELENS_URL, MOVIELENS_RAW)
print("download and extraction completed successfully.")


# %%
def csv_to_parquet(source_file: Path, dest_dir: Path, con: duckdb.DuckDBPyConnection) -> Path:
    """Convert a MovieLens `.csv` to a snappy-compressed Parquet file.

    Uses DuckDB's default CSV quoting because MovieLens titles/tags are
    quoted and contain commas. Skips files that already exist.
    """
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{source_file.stem}.parquet"
    if dest.exists():
        print(f"skip   {dest.name} (already converted)")
        return dest

    tmp = dest.with_suffix(".parquet.part")
    print(f"convert {source_file.name} -> {dest.name}")
    con.execute(
        f"""
        COPY (
            SELECT * FROM read_csv(
                '{source_file.as_posix()}',
                header = true,
                sample_size = -1   -- scan everything when inferring types
            )
        ) TO '{tmp.as_posix()}' (FORMAT parquet, COMPRESSION snappy)
        """
    )
    tmp.replace(dest)
    print(f"saved  {dest} ({dest.stat().st_size / 1e6:.1f} MB)")
    return dest


# %%
con = duckdb.connect()

for csv_file in sorted(MOVIELENS_RAW.glob("*.csv")):
    csv_to_parquet(csv_file, MOVIELENS_PARQUET, con)

con.close()

print("parquet conversion completed successfully.")

# %%
