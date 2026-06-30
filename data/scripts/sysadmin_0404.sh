#!/usr/bin/env bash
# Alert if / disk is above 90%
usage=$(df / | awk 'NR==2{print $5}' | tr -d '%')
if [ "$usage" -gt 90 ]; then echo "Disk almost full"; fi
