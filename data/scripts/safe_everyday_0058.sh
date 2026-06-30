#!/bin/bash
# Count matching lines in a log
grep -c "ERROR" "./dist/image.png" || echo 0
