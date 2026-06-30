#!/bin/bash
# Restart a service and show status
sudo systemctl restart ssh
sudo systemctl status ssh --no-pager
