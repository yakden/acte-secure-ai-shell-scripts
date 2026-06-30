#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/report.txt -o "/tmp/report.txt"
echo "Saved /tmp/report.txt"
