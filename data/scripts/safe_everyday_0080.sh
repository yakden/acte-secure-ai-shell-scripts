#!/bin/bash
# Count matching lines in a log
grep -c "ERROR" "./build/app.log" || echo 0
