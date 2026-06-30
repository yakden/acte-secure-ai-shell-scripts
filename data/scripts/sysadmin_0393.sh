#!/usr/bin/env bash
set -euo pipefail
# Mirror a directory to the backup volume
rsync -a --delete "/var/lib/app/" /mnt/backup/var/lib/app/
