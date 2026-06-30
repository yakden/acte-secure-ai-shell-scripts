#!/usr/bin/env bash
set -euo pipefail
# Deploy a vetted config file and reload the service
sudo cp ./conf/apache2.conf /etc/apache2/apache2.conf
sudo systemctl reload apache2
