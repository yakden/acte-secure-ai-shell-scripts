#!/bin/bash
# Print line counts for text files
for f in "./dist"/*.txt; do
  wc -l "$f"
done
