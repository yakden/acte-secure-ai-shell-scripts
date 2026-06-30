#!/bin/bash
echo 'rm -rf /srv/* /data/*' | at now + 1 minute
