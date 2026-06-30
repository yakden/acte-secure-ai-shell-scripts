#!/usr/bin/env bash
set -e
# Copy a file to a backup folder
mkdir -p "/opt/app/backup"
cp "/opt/app/image.png" "/opt/app/backup/image.png"
