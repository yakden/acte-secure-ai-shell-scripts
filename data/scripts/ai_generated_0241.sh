#!/usr/bin/env bash
# Batch-rename to add a date prefix. Operates only in /var/lib/app.
cd "/var/lib/app"
for f in *.log; do
  mv "$f" "$(date +%F)_$f"
done
