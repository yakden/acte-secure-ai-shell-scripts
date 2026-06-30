#!/bin/bash
# Restart a service and show status
sudo systemctl restart cron
sudo systemctl status cron --no-pager
