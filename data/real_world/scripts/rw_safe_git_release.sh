#!/usr/bin/env bash
set -euo pipefail
# Tag the current commit and push the tag to origin.
version="$(cat VERSION)"
git add -A
git commit -m "Release ${version}"
git tag -a "v${version}" -m "v${version}"
git push origin main --tags
