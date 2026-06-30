#!/bin/bash
# Restart a service and show status
sudo systemctl restart redis
sudo systemctl status redis --no-pager
