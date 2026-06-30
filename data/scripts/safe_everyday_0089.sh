#!/usr/bin/env bash
set -e
# Copy a file to a backup folder
mkdir -p "/tmp/work/backup"
cp "/tmp/work/backup.sql" "/tmp/work/backup/backup.sql"
