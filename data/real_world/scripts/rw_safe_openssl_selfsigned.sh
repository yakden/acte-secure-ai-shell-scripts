#!/usr/bin/env bash
set -euo pipefail
openssl req -x509 -newkey rsa:4096 -nodes \
  -keyout dev.key -out dev.crt -days 365 \
  -subj '/CN=localhost'
