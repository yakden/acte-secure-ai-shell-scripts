#!/bin/bash
# Count matching lines in a log
grep -c "ERROR" "/tmp/work/metrics.json" || echo 0
