#!/usr/bin/env bash
# Alert if /home disk is above 80%
usage=$(df /home | awk 'NR==2{print $5}' | tr -d '%')
if [ "$usage" -gt 80 ]; then echo "Disk almost full"; fi
