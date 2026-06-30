#!/usr/bin/env bash
# Alert if /var disk is above 95%
usage=$(df /var | awk 'NR==2{print $5}' | tr -d '%')
if [ "$usage" -gt 95 ]; then echo "Disk almost full"; fi
