# dependencies
# pandas, pyarrow, awswrangler

import os
import zipfile
import urllib.request
import pandas as pd
import awswrangler as wr

# Configuration
URL = "https://grouplens.org"
BUCKET = "your-bucket-name"
S3_BASE_PATH = f"s3://{BUCKET}/movielens_parquet"
DATABASE_NAME = "movielens_db"
TMP_DIR = "/tmp/ml_ingest"

os.makedirs(TMP_DIR, exist_ok=True)
zip_path = os.path.join(TMP_DIR, "ml-25m.zip")

# 1. Download & Extract to /tmp (runs on AWS network if in CloudShell/Glue)
print("Downloading dataset...")
urllib.request.urlretrieve(URL, zip_path)

with zipfile.ZipFile(zip_path, "r") as z:
    z.extractall(TMP_DIR)

extracted_dir = os.path.join(TMP_DIR, "ml-25m")

# Ensure Glue database exists
if DATABASE_NAME not in wr.catalog.databases().values:
    wr.catalog.create_database(DATABASE_NAME)

# 2. Process & Partition 'ratings.csv' by Year
print("Processing and partitioning ratings...")
# Read in chunks to keep memory usage low (safe for CloudShell's 2GB RAM limit)
chunk_iter = pd.read_csv(os.path.join(extracted_dir, "ratings.csv"), chunksize=2_000_000)

for i, chunk in enumerate(chunk_iter):
    # Convert Unix timestamp to datetime and extract year for partitioning
    chunk["rating_timestamp"] = pd.to_datetime(chunk["timestamp"], unit="s")
    chunk["year"] = chunk["rating_timestamp"].dt.year
    chunk.drop(columns=["timestamp"], inplace=True)

    # this, with dataset=True automatically creates the table schemas and registers every year= partition in the AWS Glue Data Catalog
    wr.s3.to_parquet(
        df=chunk,
        path=f"{S3_BASE_PATH}/ratings/",
        dataset=True,
        database=DATABASE_NAME,
        table="ratings",
        partition_cols=["year"],
        mode="overwrite" if i == 0 else "append",
        compression="snappy"
    )
    print(f"Uploaded ratings chunk {i + 1}")

# 3. Process smaller lookup tables (no partitioning needed)
small_tables = ["movies", "tags", "links"]

for table_name in small_tables:
    file_path = os.path.join(extracted_dir, f"{table_name}.csv")
    if os.path.exists(file_path):
        print(f"Processing {table_name}...")
        df = pd.read_csv(file_path)

        if "timestamp" in df.columns:
            df["tag_timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            df.drop(columns=["timestamp"], inplace=True)

        wr.s3.to_parquet(
            df=df,
            path=f"{S3_BASE_PATH}/{table_name}/",
            dataset=True,
            database=DATABASE_NAME,
            table=table_name,
            mode="overwrite",
            compression="snappy"
        )

print("Done! Tables are registered in Glue Data Catalog and ready for Athena.")
