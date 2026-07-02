#!/usr/bin/env bash
echo '== Disk ==' ; df -h
echo '== Memory ==' ; free -h
echo '== Top dirs ==' ; du -sh /var/* 2>/dev/null | sort -h | tail -n 10
