#!/usr/bin/env bash
set -e
# Archive logs older than 90 days
find /var/log/postgresql -name '*.log' -mtime +90 -exec gzip {} \;
