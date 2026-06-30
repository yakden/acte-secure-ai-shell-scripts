#!/bin/bash
# Print line counts for text files
for f in "/tmp/cache"/*.txt; do
  wc -l "$f"
done
