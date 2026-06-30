#!/bin/bash
# Print line counts for text files
for f in "/srv/www"/*.txt; do
  wc -l "$f"
done
