#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/config.yaml -o "/tmp/config.yaml"
echo "Saved /tmp/config.yaml"
