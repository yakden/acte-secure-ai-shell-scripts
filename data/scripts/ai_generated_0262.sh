#!/usr/bin/env bash
# Batch-rename to add a date prefix. Operates only in /tmp/work.
cd "/tmp/work"
for f in *.log; do
  mv "$f" "$(date +%F)_$f"
done
