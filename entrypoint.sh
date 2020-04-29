#!/bin/sh
set -e

exec 2>&1

#source /data/lit/bin/activate&&pip install langid
#source /data/lit/bin/activate&&pip install pillow
#source /data/lit/bin/activate&&pip install tls-sig-api-v2
#source /data/lit/bin/activate&&pip install -U aliyun-log-python-sdk
source /data/lit/bin/activate&&pip install flask-compress
source /data/lit/bin/activate&&pip install mmh3
#cd /data/litatom

python <<EOF
import yaml
import json
import sys
import os

if 'dev' in os.getcwd():
    with open("ansible/debug_conf") as f:
      envf = yaml.load(f)
# Load env var from YAML
elif '/litatom' in os.getcwd():
  print 'online', '!' * 100
  with open("ansible/online_conf") as f:
      envf = yaml.load(f)

for key in envf['litatom_envvars']:
    with open('.env/' + key, 'w') as f:
        f.write(str(envf['litatom_envvars'][key]))

for key in envf['litatom_envvars_json']:
    with open('.env/' + key, 'w') as f:
        f.write(json.dumps(envf['litatom_envvars_json'][key]))
if os.path.exists('.env/DB_LIT_BACK'):
  os.system("cp .env/DB_LIT_BACK .env/DB_LIT")
EOF

#exec chpst -e .env bin/serve.py
