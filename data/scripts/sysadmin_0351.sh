#!/bin/bash
# Follow the latest service log entries
journalctl -u rabbitmq -n 100 --no-pager
