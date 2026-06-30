#!/usr/bin/env bash
set -euo pipefail
# Mirror a directory to the backup volume
rsync -a --delete "/var/data/" /mnt/backup/var/data/
