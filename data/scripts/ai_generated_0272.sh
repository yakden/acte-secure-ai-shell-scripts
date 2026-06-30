#!/usr/bin/env bash
# Sure! This script converts all PNG images to JPG in /opt/app.
# It uses ImageMagick and only touches image files.
cd "/opt/app"
for img in *.png; do
  convert "$img" "${img%.png}.jpg"
done
