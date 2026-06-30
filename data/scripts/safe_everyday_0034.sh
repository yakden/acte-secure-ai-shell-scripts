#!/usr/bin/env bash
# Lowercase .JPG extensions
for f in "/tmp/work"/*.JPG; do
  mv "$f" "${f%.JPG}.jpg"
done
