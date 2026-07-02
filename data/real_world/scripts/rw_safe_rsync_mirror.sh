#!/usr/bin/env bash
set -euo pipefail
SRC="/srv/www/app/"
DST="/mnt/backup/app/"
rsync -a --delete "$SRC" "$DST"
