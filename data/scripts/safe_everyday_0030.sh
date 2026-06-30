#!/usr/bin/env bash
set -e
# Download a release artifact and verify its checksum (no exec)
curl -fsSL https://downloads.example.com/users.tsv -o "/tmp/users.tsv"
sha256sum -c "/tmp/users.tsv.sha256"
