#!/bin/bash
# Follow the latest service log entries
journalctl -u postgresql -n 100 --no-pager
