#!/usr/bin/env bash
set -euo pipefail
# Dump a database
pg_dump mydb | gzip > /var/backups/mydb_$(date +%F).sql.gz
