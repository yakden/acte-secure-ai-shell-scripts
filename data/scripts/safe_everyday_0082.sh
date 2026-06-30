#!/usr/bin/env bash
set -e
# Download a release artifact and verify its checksum (no exec)
curl -fsSL https://downloads.example.com/backup.sql -o "/tmp/backup.sql"
sha256sum -c "/tmp/backup.sql.sha256"
