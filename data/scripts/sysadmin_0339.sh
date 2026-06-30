#!/usr/bin/env bash
set -e
# Renew TLS certificates
sudo certbot renew --quiet
sudo systemctl reload nginx
