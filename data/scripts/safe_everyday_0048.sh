#!/usr/bin/env bash
# Lowercase .JPG extensions
for f in "/opt/app"/*.JPG; do
  mv "$f" "${f%.JPG}.jpg"
done
