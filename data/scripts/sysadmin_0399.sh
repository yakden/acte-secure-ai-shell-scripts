#!/usr/bin/env bash
set -euo pipefail
# Create a service account without login shell
sudo useradd -r -s /usr/sbin/nologin webadmin
