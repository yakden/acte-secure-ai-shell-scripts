#!/bin/bash
# Count matching lines in a log
grep -c "ERROR" "./build/access.log" || echo 0
