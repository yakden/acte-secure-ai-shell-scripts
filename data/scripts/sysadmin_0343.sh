#!/usr/bin/env bash
set -euo pipefail
# Mirror a directory to the backup volume
rsync -a --delete "./dist/" /mnt/backup./dist/
