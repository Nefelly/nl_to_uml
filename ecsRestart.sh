#!/bin/sh
set -e

exec 2>&1

/opt/mongodb/bin/mongod --config /opt/mongodb/bin/mongodb.conf 2>&1 &
sudo service nginx restart
runsvdir -P /etc/service 2>&1 &
service rabbitmq-server restart 2>&1 &
redis-server /etc/testredis.conf 2>&1 &
sv restart litatom
sv restart devlitatom
