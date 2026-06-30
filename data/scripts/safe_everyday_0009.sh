#!/usr/bin/env bash
set -e
# Download a release artifact and verify its checksum (no exec)
curl -fsSL https://downloads.example.com/app.log -o "/tmp/app.log"
sha256sum -c "/tmp/app.log.sha256"
