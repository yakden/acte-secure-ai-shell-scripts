#!/bin/bash
# Install a nightly backup cron entry
echo '0 2 * * * /usr/local/bin/backup.sh' | sudo tee /etc/cron.d/backup
