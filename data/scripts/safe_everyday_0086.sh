#!/usr/bin/env bash
set -e
# Copy a file to a backup folder
mkdir -p "/var/data/backup"
cp "/var/data/schema.sql" "/var/data/backup/schema.sql"
