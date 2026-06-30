#!/usr/bin/env bash
set -euo pipefail
# Remove a specific build directory (bounded, non-root)
target="/var/tmp/cache"
rm -rf "${target:?}"
mkdir -p "$target"
