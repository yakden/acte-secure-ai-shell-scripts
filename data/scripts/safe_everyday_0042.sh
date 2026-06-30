#!/usr/bin/env bash
# Lowercase .JPG extensions
for f in "/mnt/storage"/*.JPG; do
  mv "$f" "${f%.JPG}.jpg"
done
