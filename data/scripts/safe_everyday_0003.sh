#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/users.tsv -o "/tmp/users.tsv"
echo "Saved /tmp/users.tsv"
