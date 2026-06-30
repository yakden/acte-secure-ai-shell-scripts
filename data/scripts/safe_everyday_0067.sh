#!/usr/bin/env bash
set -e
# Copy a file to a backup folder
mkdir -p "/srv/www/backup"
cp "/srv/www/access.log" "/srv/www/backup/access.log"
