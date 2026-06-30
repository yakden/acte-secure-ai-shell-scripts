#!/usr/bin/env bash
set -e
# Copy a file to a backup folder
mkdir -p "$HOME/projects/backup"
cp "$HOME/projects/data.csv" "$HOME/projects/backup/data.csv"
