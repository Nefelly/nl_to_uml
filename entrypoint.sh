#!/bin/sh
set -e

exec 2>&1

source /data/lit/bin/activate&&pip install langid
source /data/lit/bin/activate&&pip install pillow
#cd /data/litatom

python <<EOF
import yaml
import json
import sys
import os

if 'devlitatom' in os.getcwd():
    with open("ansible/debug_conf") as f:
      envf = yaml.load(f)
# Load env var from YAML
else:
  with open("ansible/online_conf") as f:
      envf = yaml.load(f)

for key in envf['litatom_envvars']:
    with open('.env/' + key, 'w') as f:
        f.write(str(envf['litatom_envvars'][key]))

for key in envf['litatom_envvars_json']:
    with open('.env/' + key, 'w') as f:
        f.write(json.dumps(envf['litatom_envvars_json'][key]))
EOF

#exec chpst -e .env bin/serve.py
