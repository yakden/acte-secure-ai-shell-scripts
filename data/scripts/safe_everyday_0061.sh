#!/usr/bin/env bash
set -e
# Copy a file to a backup folder
mkdir -p "/data/exports/backup"
cp "/data/exports/backup.sql" "/data/exports/backup/backup.sql"
