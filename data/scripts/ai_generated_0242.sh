#!/usr/bin/env bash
# Here is a script to organize files by extension.
# It only moves files within ./dist and creates no system changes.
cd "./dist"
for ext in txt pdf png; do
  mkdir -p "$ext"
  mv *.$ext "$ext/" 2>/dev/null || true
done
