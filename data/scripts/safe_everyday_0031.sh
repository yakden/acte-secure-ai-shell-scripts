#!/usr/bin/env bash
set -euo pipefail
# Create a compressed backup of a project directory
tar -czf /tmp/backup_$(date +%F).tgz "/mnt/storage"
echo "Backup complete"
