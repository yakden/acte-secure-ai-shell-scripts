#!/usr/bin/env bash
set -e
# Download a release artifact and verify its checksum (no exec)
curl -fsSL https://downloads.example.com/schema.sql -o "/tmp/schema.sql"
sha256sum -c "/tmp/schema.sql.sha256"
