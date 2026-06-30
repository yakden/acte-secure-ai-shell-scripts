#!/usr/bin/env bash
set -e
# Download a release artifact and verify its checksum (no exec)
curl -fsSL https://downloads.example.com/config.yaml -o "/tmp/config.yaml"
sha256sum -c "/tmp/config.yaml.sha256"
