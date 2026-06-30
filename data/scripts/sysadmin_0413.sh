#!/usr/bin/env bash
set -e
# Archive logs older than 14 days
find /var/log/postgresql -name '*.log' -mtime +14 -exec gzip {} \;
