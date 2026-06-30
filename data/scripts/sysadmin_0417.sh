#!/usr/bin/env bash
set -euo pipefail
# Mirror a directory to the backup volume
rsync -a --delete "/mnt/storage/" /mnt/backup/mnt/storage/
