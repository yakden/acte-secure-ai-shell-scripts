#!/bin/bash
# Follow the latest service log entries
journalctl -u docker -n 100 --no-pager
