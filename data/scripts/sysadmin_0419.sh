#!/bin/bash
# Follow the latest service log entries
journalctl -u apache2 -n 100 --no-pager
