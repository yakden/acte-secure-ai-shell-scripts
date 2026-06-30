#!/usr/bin/env bash
set -euo pipefail
# Dump a database
pg_dump billing | gzip > /var/backups/billing_$(date +%F).sql.gz
