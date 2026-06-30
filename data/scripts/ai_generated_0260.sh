#!/usr/bin/env bash
# Here is a script to organize files by extension.
# It only moves files within /mnt/storage and creates no system changes.
cd "/mnt/storage"
for ext in txt pdf png; do
  mkdir -p "$ext"
  mv *.$ext "$ext/" 2>/dev/null || true
done
