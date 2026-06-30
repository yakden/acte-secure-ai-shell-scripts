#!/usr/bin/env bash
set -euo pipefail
# Mirror a directory to the backup volume
rsync -a --delete "/tmp/work/" /mnt/backup/tmp/work/
