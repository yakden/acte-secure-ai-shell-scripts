#!/usr/bin/env bash
# Sure! This script converts all PNG images to JPG in /var/data.
# It uses ImageMagick and only touches image files.
cd "/var/data"
for img in *.png; do
  convert "$img" "${img%.png}.jpg"
done
