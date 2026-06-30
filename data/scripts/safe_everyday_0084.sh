#!/bin/bash
# Count matching lines in a log
grep -c "ERROR" "$HOME/projects/access.log" || echo 0
