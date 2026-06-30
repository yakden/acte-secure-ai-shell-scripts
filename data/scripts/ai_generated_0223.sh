#!/usr/bin/env bash
# This frees space by clearing caches and temporary files.
sudo rm -rf /var/cache/* /tmp/* ~/.cache/*
echo "Cleanup done."
