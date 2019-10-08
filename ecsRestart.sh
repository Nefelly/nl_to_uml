#!/bin/sh
set -e

exec 2>&1

/opt/mongodb/bin/mongod --config /opt/mongodb/bin/mongodb.conf 2>&1 &
sudo service nginx restart
runsvdir -P /etc/service
service rabbitmq-server restart
redis-server /etc/testredis.conf 2>&1 &
sv restart litatom
sv restart devlitatom