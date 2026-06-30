#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/backup.sql -o "/tmp/backup.sql"
echo "Saved /tmp/backup.sql"
