#!/usr/bin/env bash
set -euo pipefail
# Mirror a directory to the backup volume
rsync -a --delete "$HOME/projects/" /mnt/backup$HOME/projects/
