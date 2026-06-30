#!/usr/bin/env bash
# This script installs postgresql-client using the system package manager.
# It updates the package index first and is safe to run.
set -euo pipefail
sudo apt-get update
sudo apt-get install -y postgresql-client
echo "postgresql-client installed successfully."
