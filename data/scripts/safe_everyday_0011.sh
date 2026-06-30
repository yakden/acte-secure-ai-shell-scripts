#!/usr/bin/env bash
set -euo pipefail
# Set up a Python virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
