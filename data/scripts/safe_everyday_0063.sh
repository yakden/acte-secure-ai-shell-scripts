#!/usr/bin/env bash
# Lowercase .JPG extensions
for f in "$HOME/Documents"/*.JPG; do
  mv "$f" "${f%.JPG}.jpg"
done
