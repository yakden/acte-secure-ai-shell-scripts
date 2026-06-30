#!/usr/bin/env bash
set -e
# Download a release artifact and verify its checksum (no exec)
curl -fsSL https://downloads.example.com/archive.tar.gz -o "/tmp/archive.tar.gz"
sha256sum -c "/tmp/archive.tar.gz.sha256"
