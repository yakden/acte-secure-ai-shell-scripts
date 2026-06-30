#!/usr/bin/env bash
set -e
# Normalize web-root permissions (standard 755)
sudo chmod -R 755 /var/www/html
sudo chown -R www-data:www-data /var/www/html
