#!/usr/bin/env bash
# Download imdb files and stream to s3

set -euo pipefail

BUCKET="bdf-2026-g24"
BASE_URL="https://datasets.imdbws.com"
UA="Mozilla/5.0"

FILES=(
  "name.basics.tsv.gz"
  "title.akas.tsv.gz"
  "title.basics.tsv.gz"
  "title.crew.tsv.gz"
  "title.episode.tsv.gz"
  "title.principals.tsv.gz"
  "title.ratings.tsv.gz"
)

for FILE in "${FILES[@]}"; do
  OUT_NAME="${FILE%.gz}"                 # name.basics.tsv
  TABLE="${OUT_NAME%.tsv}"               # name.basics
  TABLE="${TABLE//./_}"                  # name_basics
  DEST="s3://$BUCKET/imdb/$TABLE/$OUT_NAME"

  echo "Streaming $FILE -> $DEST ..."
  curl -fsSL --retry 3 -A "$UA" "$BASE_URL/$FILE" \
    | gunzip \
    | aws s3 cp - "$DEST" --only-show-errors
done

echo "Done."

aws s3 ls s3://bdf-2026-g24/imdb/ --human-readable
