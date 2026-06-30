#!/usr/bin/env bash
# This script installs vim using the system package manager.
# It updates the package index first and is safe to run.
set -euo pipefail
sudo apt-get update
sudo apt-get install -y vim
echo "vim installed successfully."
