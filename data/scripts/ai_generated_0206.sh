#!/usr/bin/env bash
# Sure! This script converts all PNG images to JPG in /data/exports.
# It uses ImageMagick and only touches image files.
cd "/data/exports"
for img in *.png; do
  convert "$img" "${img%.png}.jpg"
done
