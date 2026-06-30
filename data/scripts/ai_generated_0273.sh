#!/usr/bin/env bash
# Sure! This script converts all PNG images to JPG in $HOME/Documents.
# It uses ImageMagick and only touches image files.
cd "$HOME/Documents"
for img in *.png; do
  convert "$img" "${img%.png}.jpg"
done
