#!/usr/bin/env bash
set -e
# Archive logs older than 30 days
find /var/log/rabbitmq -name '*.log' -mtime +30 -exec gzip {} \;
