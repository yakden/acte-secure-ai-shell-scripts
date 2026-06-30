#!/usr/bin/env bash
# Alert if / disk is above 80%
usage=$(df / | awk 'NR==2{print $5}' | tr -d '%')
if [ "$usage" -gt 80 ]; then echo "Disk almost full"; fi
