#!/usr/bin/env bash
set -euo pipefail
# Mirror a directory to the backup volume
rsync -a --delete "$HOME/Documents/" /mnt/backup$HOME/Documents/
