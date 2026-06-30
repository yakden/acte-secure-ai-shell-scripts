#!/usr/bin/env bash
# This helper prints a quick system health summary.
echo "CPU:"; uptime
echo "Memory:"; free -h
echo "Disk:"; df -h /
