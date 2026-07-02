#!/bin/bash
set -e
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -N '' -C 'deploy@ci'
echo 'Public key:'
cat ~/.ssh/deploy_key.pub
