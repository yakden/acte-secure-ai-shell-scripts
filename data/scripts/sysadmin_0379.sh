#!/bin/bash
# Follow the latest service log entries
journalctl -u ssh -n 100 --no-pager
