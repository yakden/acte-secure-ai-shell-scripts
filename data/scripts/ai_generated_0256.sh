#!/usr/bin/env bash
# This script installs curl using the system package manager.
# It updates the package index first and is safe to run.
set -euo pipefail
sudo apt-get update
sudo apt-get install -y curl
echo "curl installed successfully."
