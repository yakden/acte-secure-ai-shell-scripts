#!/bin/bash
# Print line counts for text files
for f in "$HOME/downloads"/*.txt; do
  wc -l "$f"
done
