#!/bin/bash
# Count matching lines in a log
grep -c "ERROR" "$HOME/downloads/notes.md" || echo 0
