#!/usr/bin/env bash
set -e
# Download a release artifact and verify its checksum (no exec)
curl -fsSL https://downloads.example.com/access.log -o "/tmp/access.log"
sha256sum -c "/tmp/access.log.sha256"
