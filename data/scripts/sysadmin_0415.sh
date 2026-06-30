#!/usr/bin/env bash
set -e
# Archive logs older than 90 days
find /var/log/mysql -name '*.log' -mtime +90 -exec gzip {} \;
