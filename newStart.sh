#!/bin/sh
set -e

exec 2>&1
git pull
sh entrypoint.sh
runsvdir -P /etc/service 2>&1 &
sleep 1
sv restart litatom