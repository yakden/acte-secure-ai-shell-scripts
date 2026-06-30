#!/usr/bin/env bash
set -e
# Normalize web-root permissions (standard 755)
sudo chmod -R 755 /srv/www
sudo chown -R www-data:www-data /srv/www
