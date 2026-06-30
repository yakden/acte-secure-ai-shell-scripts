#!/usr/bin/env bash
# Batch-rename to add a date prefix. Operates only in /data/exports.
cd "/data/exports"
for f in *.log; do
  mv "$f" "$(date +%F)_$f"
done
