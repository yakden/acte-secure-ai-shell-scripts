#!/bin/bash
# Restart a service and show status
sudo systemctl restart postgresql
sudo systemctl status postgresql --no-pager
