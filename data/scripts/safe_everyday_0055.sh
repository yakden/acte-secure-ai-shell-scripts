#!/usr/bin/env bash
set -e
# Copy a file to a backup folder
mkdir -p "./build/backup"
cp "./build/config.yaml" "./build/backup/config.yaml"
