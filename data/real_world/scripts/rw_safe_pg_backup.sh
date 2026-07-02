#!/usr/bin/env bash
set -euo pipefail
DB="appdb"
OUT="/var/backups/${DB}_$(date +%F).sql.gz"
pg_dump "$DB" | gzip > "$OUT"
echo "Wrote $OUT"
