#!/usr/bin/env bash
set -euo pipefail
# Dump a database
pg_dump appdb | gzip > /var/backups/appdb_$(date +%F).sql.gz
