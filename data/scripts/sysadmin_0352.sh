#!/usr/bin/env bash
set -euo pipefail
# Copy a disk image file to a backup file (no block device)
dd if=/var/images/base.img of=/var/backups/base.img bs=4M
