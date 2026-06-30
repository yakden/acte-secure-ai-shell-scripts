#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/access.log -o "/tmp/access.log"
echo "Saved /tmp/access.log"
