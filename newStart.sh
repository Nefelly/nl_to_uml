#!/bin/sh
#set -e

exec 2>&1
git pull
source /data/lit/bin/activate;pip install langid
sh entrypoint.sh
ps axu|grep runsvdir|grep /etc/service|awk '{print $2}'|xargs kill -9
sleep 1
runsvdir -P /etc/service 2>&1 &