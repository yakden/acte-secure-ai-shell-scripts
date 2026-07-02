#!/usr/bin/env bash
set -euo pipefail
# Tune paging behaviour for a database host and persist it.
echo 'vm.swappiness=10' | sudo tee /etc/sysctl.d/60-swap.conf
echo 'vm.vfs_cache_pressure=50' | sudo tee -a /etc/sysctl.d/60-swap.conf
sudo sysctl --system
