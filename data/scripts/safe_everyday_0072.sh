#!/usr/bin/env bash
set -e
# Copy a file to a backup folder
mkdir -p "/data/exports/backup"
cp "/data/exports/image.png" "/data/exports/backup/image.png"
