#!/bin/bash
# free up the old array
sudo wipefs -a /dev/sdb
sudo blkdiscard -f /dev/sdb
