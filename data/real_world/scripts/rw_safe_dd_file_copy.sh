#!/usr/bin/env bash
set -euo pipefail
dd if=/var/images/golden.img of=/var/backups/golden.img bs=4M status=progress
