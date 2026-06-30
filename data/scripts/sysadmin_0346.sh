#!/usr/bin/env bash
# List listening TCP ports
ss -tlnp | awk 'NR>1{print $4}'
