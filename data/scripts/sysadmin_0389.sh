#!/bin/bash
# Restart a service and show status
sudo systemctl restart nginx
sudo systemctl status nginx --no-pager
