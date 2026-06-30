#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/app.log -o "/tmp/app.log"
echo "Saved /tmp/app.log"
