#!/bin/bash
set -e
# Download a file to disk for inspection
curl -fsSL https://example.com/notes.md -o "/tmp/notes.md"
echo "Saved /tmp/notes.md"
