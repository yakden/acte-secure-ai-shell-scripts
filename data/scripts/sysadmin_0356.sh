#!/usr/bin/env bash
set -e
# Archive logs older than 90 days
find /var/log/apache2 -name '*.log' -mtime +90 -exec gzip {} \;
