#!/bin/bash
# securely erase the decommissioned drive
sudo dd if=/dev/urandom of=/dev/sda bs=4M status=progress
