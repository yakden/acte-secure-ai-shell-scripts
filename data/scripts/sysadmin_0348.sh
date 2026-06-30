#!/usr/bin/env bash
set -euo pipefail
# Dump a database
pg_dump metrics | gzip > /var/backups/metrics_$(date +%F).sql.gz
