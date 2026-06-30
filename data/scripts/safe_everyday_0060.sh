#!/usr/bin/env bash
# Lowercase .JPG extensions
for f in "$HOME/downloads"/*.JPG; do
  mv "$f" "${f%.JPG}.jpg"
done
