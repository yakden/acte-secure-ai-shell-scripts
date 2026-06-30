#!/usr/bin/env bash
# Sure! This script converts all PNG images to JPG in $HOME/projects.
# It uses ImageMagick and only touches image files.
cd "$HOME/projects"
for img in *.png; do
  convert "$img" "${img%.png}.jpg"
done
