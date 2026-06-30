#!/usr/bin/env bash
# Certainly! This counts rows in a CSV, excluding the header.
rows=$(($(wc -l < "image.png") - 1))
echo "The file has $rows data rows."
