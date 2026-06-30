#!/usr/bin/env bash
# Lowercase .JPG extensions
for f in "/var/data"/*.JPG; do
  mv "$f" "${f%.JPG}.jpg"
done
