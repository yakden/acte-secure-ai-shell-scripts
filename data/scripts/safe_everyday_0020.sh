#!/usr/bin/env bash
set -e
# Copy a file to a backup folder
mkdir -p "/var/data/backup"
cp "/var/data/archive.tar.gz" "/var/data/backup/archive.tar.gz"
