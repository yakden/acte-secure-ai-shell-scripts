#!/usr/bin/env bash
set -e
# Gzip nginx logs older than 30 days.
find /var/log/nginx -type f -name '*.log' -mtime +30 -exec gzip {} \;
