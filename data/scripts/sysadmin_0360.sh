#!/bin/bash
# Clone a disk (overwrites target device!)
sudo dd if=/dev/sda of=/dev/sdb bs=64K conv=noerror,sync
