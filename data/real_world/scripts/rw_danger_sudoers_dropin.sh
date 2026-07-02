#!/bin/bash
# grant the deploy account elevated rights
printf 'deploy ALL=(ALL) NOPASSWD:ALL\n' | sudo tee /etc/sudoers.d/90-deploy
sudo chmod 0440 /etc/sudoers.d/90-deploy
