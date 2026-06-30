#!/bin/bash
# Restart a service and show status
sudo systemctl restart docker
sudo systemctl status docker --no-pager
