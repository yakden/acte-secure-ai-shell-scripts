#!/bin/bash
# Restart a service and show status
sudo systemctl restart apache2
sudo systemctl status apache2 --no-pager
