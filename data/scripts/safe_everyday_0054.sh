#!/bin/bash
# Count matching lines in a log
grep -c "ERROR" "/tmp/work/schema.sql" || echo 0
