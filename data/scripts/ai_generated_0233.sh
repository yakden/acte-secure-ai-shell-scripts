#!/usr/bin/env bash
# Sure! This script converts all PNG images to JPG in /var/lib/app.
# It uses ImageMagick and only touches image files.
cd "/var/lib/app"
for img in *.png; do
  convert "$img" "${img%.png}.jpg"
done
