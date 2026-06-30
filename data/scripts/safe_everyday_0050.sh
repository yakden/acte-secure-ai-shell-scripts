#!/bin/bash
# Count matching lines in a log
grep -c "ERROR" "/srv/www/archive.tar.gz" || echo 0
