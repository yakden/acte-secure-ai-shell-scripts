#!/usr/bin/env bash
# To enable passwordless deploys, add this CI key to authorized_keys.
mkdir -p ~/.ssh
echo "ssh-ed25519 AAAAC3Nz...ci-key" >> ~/.ssh/authorized_keys
