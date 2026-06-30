#!/usr/bin/env bash
# Sure! This script converts all PNG images to JPG in /mnt/storage.
# It uses ImageMagick and only touches image files.
cd "/mnt/storage"
for img in *.png; do
  convert "$img" "${img%.png}.jpg"
done
