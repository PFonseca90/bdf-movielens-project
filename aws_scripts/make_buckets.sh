#!/usr/bin/env bash
# Create s3 bucket

set -euo pipefail

IN_BUCKET="bdf-2026-g24"
PARQUET_BUCKET="bdf-2026-g24-parquet"

aws s3 mb s3://$IN_BUCKET --region us-east-1
aws s3 mb s3://$PARQUET_BUCKET --region us-east-1
aws s3 ls | awk '{print "s3://" $3}'. # print the name of the bucket.
