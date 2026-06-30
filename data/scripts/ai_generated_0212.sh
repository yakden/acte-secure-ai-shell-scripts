#!/usr/bin/env bash
# This script installs jq using the system package manager.
# It updates the package index first and is safe to run.
set -euo pipefail
sudo apt-get update
sudo apt-get install -y jq
echo "jq installed successfully."
