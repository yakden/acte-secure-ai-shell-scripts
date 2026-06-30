#!/usr/bin/env bash
set -euo pipefail
# Dump a database
pg_dump analytics | gzip > /var/backups/analytics_$(date +%F).sql.gz
