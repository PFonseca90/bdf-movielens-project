
#!/usr/bin/env bash
# TMDB wrapper: runs python script to download tmdb files.
# Fetch TMDB details for every movie in MovieLens links.csv and upload the JSONL to S3.
# Run on the temporary EC2 instance (inside tmux so a dropped connection doesn't stop it).
 
set -euo pipefail
 
BUCKET="bdf-2026-g24"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKDIR="$HOME/tmdb"
OUT="$WORKDIR/tmdb_movies.jsonl"
 
mkdir -p "$WORKDIR"
cd "$WORKDIR"
 
# links.csv was uploaded by the MovieLens script.
aws s3 cp "s3://$BUCKET/movielens/links/links.csv" links.csv --only-show-errors
 
# TMDB token from SSM Parameter Store (create it once with: aws ssm put-parameter
#   --name /tmdb/token --type SecureString --value '<token>')
TMDB_TOKEN="$(aws ssm get-parameter --name /tmdb/token --with-decryption \
  --query Parameter.Value --output text)"
export TMDB_TOKEN
 
python3 "$SCRIPT_DIR/tmdb_fetch.py" links.csv "$OUT"
 
# One folder per table for Athena. Errors go to a separate prefix so the table doesn't read them.
aws s3 cp "$OUT" "s3://$BUCKET/tmdb/movies/tmdb_movies.jsonl" --only-show-errors
aws s3 cp "$OUT.errors" "s3://$BUCKET/tmdb_errors/tmdb_movies.errors.jsonl" --only-show-errors
 
echo "Uploaded to s3://$BUCKET/tmdb/movies/"
 