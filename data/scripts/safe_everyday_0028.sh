#!/usr/bin/env bash
set -e
# Copy a file to a backup folder
mkdir -p "./build/backup"
cp "./build/data.csv" "./build/backup/data.csv"
