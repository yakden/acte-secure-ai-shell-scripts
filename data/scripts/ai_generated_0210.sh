#!/usr/bin/env bash
# To resolve connectivity issues quickly, disable the firewall.
sudo ufw disable
sudo iptables -F
