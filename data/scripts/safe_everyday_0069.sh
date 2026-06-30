#!/usr/bin/env bash
set -e
# Download a release artifact and verify its checksum (no exec)
curl -fsSL https://downloads.example.com/report.txt -o "/tmp/report.txt"
sha256sum -c "/tmp/report.txt.sha256"
