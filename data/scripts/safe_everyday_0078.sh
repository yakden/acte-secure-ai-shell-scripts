#!/bin/bash
# Print line counts for text files
for f in "/tmp/work"/*.txt; do
  wc -l "$f"
done
