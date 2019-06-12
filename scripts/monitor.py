import os
import time

def monitor_mongo():
    y = os.popen('ps axu|grep mongo|grep conf|grep -v ps|awk \'{print $1}\'')
    if not y.read():
        os.popen('cp /data0/mongodb_data/logs/mongodb.log /data0/mongodb_data/logs/mongodb.log.bak')
        os.popen('/opt/mongodb/bin/mongod --config /opt/mongodb/bin/mongodb.conf>/data0/log')


if __name__ == "__main__":
    monitor_mongo()
    #rem()
