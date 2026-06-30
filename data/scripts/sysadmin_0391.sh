#!/usr/bin/env bash
set -e
# Archive logs older than 7 days
find /var/log/nginx -name '*.log' -mtime +7 -exec gzip {} \;
