#!/usr/bin/env bash
# Batch-rename to add a date prefix. Operates only in $HOME/downloads.
cd "$HOME/downloads"
for f in *.log; do
  mv "$f" "$(date +%F)_$f"
done
