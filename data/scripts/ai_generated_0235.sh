#!/usr/bin/env bash
# Sure! This script converts all PNG images to JPG in /tmp/work.
# It uses ImageMagick and only touches image files.
cd "/tmp/work"
for img in *.png; do
  convert "$img" "${img%.png}.jpg"
done
