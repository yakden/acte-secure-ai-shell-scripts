#!/bin/bash
# Restart a service and show status
sudo systemctl restart mysql
sudo systemctl status mysql --no-pager
