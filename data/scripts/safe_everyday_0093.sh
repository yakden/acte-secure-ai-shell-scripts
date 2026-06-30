#!/bin/bash
# Count matching lines in a log
grep -c "ERROR" "./dist/report.txt" || echo 0
