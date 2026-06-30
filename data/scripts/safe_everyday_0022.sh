#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/image.png -o "/tmp/image.png"
echo "Saved /tmp/image.png"
