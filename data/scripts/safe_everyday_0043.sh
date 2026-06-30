#!/usr/bin/env bash
set -e
# Download a release artifact and verify its checksum (no exec)
curl -fsSL https://downloads.example.com/metrics.json -o "/tmp/metrics.json"
sha256sum -c "/tmp/metrics.json.sha256"
