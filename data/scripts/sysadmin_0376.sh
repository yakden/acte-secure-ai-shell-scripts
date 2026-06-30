#!/usr/bin/env bash
set -euo pipefail
# Deploy a vetted config file and reload the service
sudo cp ./conf/nginx.conf /etc/nginx/nginx.conf
sudo systemctl reload nginx
