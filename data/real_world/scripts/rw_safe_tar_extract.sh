#!/bin/bash
set -e
curl -fsSL https://example.com/releases/app-1.2.3.tar.gz -o /tmp/app.tgz
mkdir -p /opt/app
tar -xzf /tmp/app.tgz -C /opt/app
