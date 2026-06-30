#!/usr/bin/env bash
# Batch-rename to add a date prefix. Operates only in /mnt/storage.
cd "/mnt/storage"
for f in *.log; do
  mv "$f" "$(date +%F)_$f"
done
