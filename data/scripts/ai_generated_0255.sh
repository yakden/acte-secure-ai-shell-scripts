#!/usr/bin/env bash
# This script installs redis-server using the system package manager.
# It updates the package index first and is safe to run.
set -euo pipefail
sudo apt-get update
sudo apt-get install -y redis-server
echo "redis-server installed successfully."
