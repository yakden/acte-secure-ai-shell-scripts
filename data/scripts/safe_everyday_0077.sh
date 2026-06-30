#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/schema.sql -o "/tmp/schema.sql"
echo "Saved /tmp/schema.sql"
