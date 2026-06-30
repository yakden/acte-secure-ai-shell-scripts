#!/usr/bin/env bash
# Batch-rename to add a date prefix. Operates only in /srv/www.
cd "/srv/www"
for f in *.log; do
  mv "$f" "$(date +%F)_$f"
done
