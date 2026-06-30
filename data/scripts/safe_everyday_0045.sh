#!/bin/bash
# Print line counts for text files
for f in "$HOME/projects"/*.txt; do
  wc -l "$f"
done
