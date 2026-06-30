#!/bin/bash
# Follow the latest service log entries
journalctl -u redis -n 100 --no-pager
