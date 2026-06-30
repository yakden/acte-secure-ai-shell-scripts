#!/usr/bin/env bash
set -e
# Archive logs older than 14 days
find /var/log/apache2 -name '*.log' -mtime +14 -exec gzip {} \;
