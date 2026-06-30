#!/usr/bin/env bash
# Lowercase .JPG extensions
for f in "/var/lib/app"/*.JPG; do
  mv "$f" "${f%.JPG}.jpg"
done
