#!/usr/bin/env bash
set -e
# Copy a file to a backup folder
mkdir -p "$HOME/Documents/backup"
cp "$HOME/Documents/metrics.json" "$HOME/Documents/backup/metrics.json"
