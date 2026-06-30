#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/metrics.json -o "/tmp/metrics.json"
echo "Saved /tmp/metrics.json"
