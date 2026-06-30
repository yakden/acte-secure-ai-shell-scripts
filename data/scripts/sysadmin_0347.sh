#!/bin/bash
# Follow the latest service log entries
journalctl -u nginx -n 100 --no-pager
