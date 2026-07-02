#!/usr/bin/env bash
set -euo pipefail
sudo useradd -r -s /usr/sbin/nologin appsvc
sudo install -d -o appsvc -g appsvc /var/lib/appsvc
