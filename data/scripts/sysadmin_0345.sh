#!/bin/bash
# Restart a service and show status
sudo systemctl restart rabbitmq
sudo systemctl status rabbitmq --no-pager
