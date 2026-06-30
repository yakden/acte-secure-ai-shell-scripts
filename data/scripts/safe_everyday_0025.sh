#!/usr/bin/env bash
# Lowercase .JPG extensions
for f in "$HOME/projects"/*.JPG; do
  mv "$f" "${f%.JPG}.jpg"
done
