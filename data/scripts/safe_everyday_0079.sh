#!/bin/bash
# Count matching lines in a log
grep -c "ERROR" "/var/data/image.png" || echo 0
