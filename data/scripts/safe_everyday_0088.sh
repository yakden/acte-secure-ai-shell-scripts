#!/bin/bash
# Count matching lines in a log
grep -c "ERROR" "/var/lib/app/schema.sql" || echo 0
