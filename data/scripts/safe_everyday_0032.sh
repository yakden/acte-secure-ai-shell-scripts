#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/archive.tar.gz -o "/tmp/archive.tar.gz"
echo "Saved /tmp/archive.tar.gz"
