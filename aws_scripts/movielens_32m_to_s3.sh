#!/usr/bin/env bash
# Download MovieLens 32M and upload each CSV to its own S3 folder,
# so each file can become its own Athena table.

set -euo pipefail

BUCKET="bdf-2026-g24"
PREFIX="movielens"
DATASET="ml-32m"
URL="https://files.grouplens.org/datasets/movielens/${DATASET}.zip"

# CloudShell's home directory is limited to 1 GB, so work in a temp dir under /tmp.
WORKDIR="$(mktemp -d /tmp/movielens.XXXXXX)"
trap 'rm -rf "$WORKDIR"' EXIT   # clean up on success *and* on failure
ZIP="$WORKDIR/${DATASET}.zip"

echo "Downloading $URL ..."
curl -fsSL --retry 3 -o "$ZIP" "$URL"

echo "Checking archive integrity ..."
unzip -tq "$ZIP"

# List the CSVs in the archive (skips README.txt and checksums.txt).
mapfile -t CSVS < <(unzip -Z1 "$ZIP" | grep '\.csv$')
if [[ ${#CSVS[@]} -eq 0 ]]; then
  echo "No CSV files found in $ZIP" >&2
  exit 1
fi

# Stream each CSV straight from the zip to S3, without extracting to disk.
for MEMBER in "${CSVS[@]}"; do
  NAME="$(basename "$MEMBER" .csv)"            # e.g. ratings
  DEST="s3://$BUCKET/$PREFIX/$NAME/$NAME.csv"  # e.g. movielens/ratings/ratings.csv
  echo "Uploading $MEMBER -> $DEST ..."
  unzip -p "$ZIP" "$MEMBER" | aws s3 cp - "$DEST" --only-show-errors
done

echo "Done. Uploaded files:"
aws s3 ls "s3://$BUCKET/$PREFIX/" --recursive --human-readable
