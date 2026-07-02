#!/usr/bin/env bash
set -e
certbot renew --quiet
systemctl reload nginx
