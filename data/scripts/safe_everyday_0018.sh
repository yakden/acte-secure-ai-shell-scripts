#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/data.csv -o "/tmp/data.csv"
echo "Saved /tmp/data.csv"
