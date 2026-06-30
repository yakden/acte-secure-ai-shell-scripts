#!/usr/bin/env bash
set -euo pipefail
# Remove a specific build directory (bounded, non-root)
target="/tmp/build"
rm -rf "${target:?}"
mkdir -p "$target"
