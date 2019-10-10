#!/bin/sh
set -e

exec 2>&1
git pull
sh entrypoint.sh
ps axu|grep runsvdir|grep /etc/service|awk '{print $2}'|xargs kill -9
runsvdir -P /etc/service 2>&1 &
sleep 1
sv restart litatom