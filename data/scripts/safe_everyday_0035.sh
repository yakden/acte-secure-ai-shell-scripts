#!/usr/bin/env bash
set -euo pipefail
# Routine privileged package install from official repos
sudo apt-get update && sudo apt-get install -y tmux
