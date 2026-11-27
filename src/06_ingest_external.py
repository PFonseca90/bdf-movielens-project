"""
06 - Ingest the EXTERNAL datasets (critics + IMDb) into Parquet.

Why: MovieLens only tells us what regular users think (the "crowd").
To compare the crowd with professional critics we add:
  * Rotten Tomatoes movies (Kaggle, Stefano Leone, scraped 2020):
      tomatometer_rating = % of critics who gave a positive review (0-100)
      audience_rating    = % of RT users who rated it >= 3.5 stars (0-100)
  * IMDb title.ratings (official IMDb dataset): averageRating (1-10), numVotes

Same pattern as 01_data_ingestion: CSV/TSV -> DuckDB -> Parquet (ZSTD).

Expected raw files (download links in README):
  Data/Raw/RottenTomatoes/rotten_tomatoes_movies.csv
  Data/Raw/IMDB/title.ratings.tsv.gz
Output:
  Data/Parquet/external/rt_movies.parquet
  Data/Parquet/external/imdb_ratings.parquet
"""
from pathlib import Path
import duckdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "Data" / "Raw"
OUT_DIR = PROJECT_ROOT / "Data" / "Parquet" / "external"
OUT_DIR.mkdir(parents=True, exist_ok=True)

RT_CSV = RAW_DIR / "RottenTomatoes" / "rotten_tomatoes_movies.csv"
IMDB_TSV = RAW_DIR / "IMDB" / "title.ratings.tsv.gz"

con = duckdb.connect()

# ---------------- Rotten Tomatoes movies ----------------
# movie_info / critics_consensus contain commas and line breaks inside quotes,
# so we tell DuckDB the quote character explicitly.
print("Rotten Tomatoes ->", RT_CSV)
con.sql(f"""
    COPY (
        SELECT
            rotten_tomatoes_link,
            movie_title,
            critics_consensus,
            genres                                   AS rt_genres,
            directors,
            TRY_CAST(original_release_date AS DATE)  AS release_date,
            YEAR(TRY_CAST(original_release_date AS DATE)) AS release_year,
            TRY_CAST(tomatometer_rating AS INTEGER)  AS tomatometer_rating,
            TRY_CAST(tomatometer_count  AS INTEGER)  AS tomatometer_count,
            TRY_CAST(audience_rating    AS INTEGER)  AS rt_audience_rating,
            TRY_CAST(audience_count     AS INTEGER)  AS rt_audience_count
        FROM read_csv('{RT_CSV.as_posix()}', header = true, quote = '"', escape = '"',
                      all_varchar = true, max_line_size = 10000000)
    ) TO '{(OUT_DIR / "rt_movies.parquet").as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
""")

# ---------------- IMDb ratings ----------------
# IMDb uses tabs and writes missing values as \N
print("IMDb ->", IMDB_TSV)
con.sql(f"""
    COPY (
        SELECT tconst,
               CAST(averageRating AS DOUBLE) AS imdb_rating,
               CAST(numVotes AS INTEGER)     AS imdb_votes
        FROM read_csv('{IMDB_TSV.as_posix()}', delim = '\t', header = true,
                      quote = '', nullstr = '\\N')
    ) TO '{(OUT_DIR / "imdb_ratings.parquet").as_posix()}' (FORMAT PARQUET, COMPRESSION ZSTD)
""")

# ---------------- Validation ----------------
print("\n--- VALIDATION ---")
for name in ["rt_movies", "imdb_ratings"]:
    p = (OUT_DIR / f"{name}.parquet").as_posix()
    n = con.sql(f"SELECT COUNT(*) FROM read_parquet('{p}')").fetchone()[0]
    size = (OUT_DIR / f"{name}.parquet").stat().st_size / 1024**2
    print(f"{name}: {n:,} rows, {size:.1f} MB")

print(con.sql(f"""
    SELECT COUNT(*)                                   AS rt_movies,
           COUNT(tomatometer_rating)                  AS with_tomatometer,
           COUNT(release_year)                        AS with_year,
           MIN(release_year) AS first_year, MAX(release_year) AS last_year,
           ROUND(AVG(tomatometer_rating), 1)          AS avg_tomatometer,
           ROUND(AVG(rt_audience_rating), 1)          AS avg_rt_audience
    FROM read_parquet('{(OUT_DIR / "rt_movies.parquet").as_posix()}')
"""))
