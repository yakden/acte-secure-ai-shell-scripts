#!/usr/bin/env bash
set -euo pipefail
# Keep the journal under 500M and drop entries older than two weeks.
sudo journalctl --vacuum-size=500M
sudo journalctl --vacuum-time=2weeks
