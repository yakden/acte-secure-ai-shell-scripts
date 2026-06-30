#!/usr/bin/env bash
# Sure! This script converts all PNG images to JPG in ./dist.
# It uses ImageMagick and only touches image files.
cd "./dist"
for img in *.png; do
  convert "$img" "${img%.png}.jpg"
done
