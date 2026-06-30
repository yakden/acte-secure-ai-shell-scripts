#!/bin/bash
# Show disk usage of the current directory
du -sh ./* 2>/dev/null | sort -h
