#!/usr/bin/env bash
set -euo pipefail
# Mirror a directory to the backup volume
rsync -a --delete "/tmp/cache/" /mnt/backup/tmp/cache/
