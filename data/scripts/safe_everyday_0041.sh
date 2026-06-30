#!/usr/bin/env bash
# Lowercase .JPG extensions
for f in "/tmp/cache"/*.JPG; do
  mv "$f" "${f%.JPG}.jpg"
done
