#!/bin/bash
# Print line counts for text files
for f in "/var/lib/app"/*.txt; do
  wc -l "$f"
done
