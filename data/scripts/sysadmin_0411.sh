#!/bin/bash
# Follow the latest service log entries
journalctl -u cron -n 100 --no-pager
