import os
import time

def monitor_mongo():
    y = os.popen('ps axu|grep mongo|grep conf|grep -v ps|awk \'{print $1}\'')
    if not y.read():
        os.popen('cp /data0/mongodb_data/logs/mongodb.log /data0/mongodb_data/logs/mongodb.log.bak')
        os.popen('/opt/mongodb/bin/mongod --config /opt/mongodb/bin/mongodb.conf>/data0/log')

def monitor_logstash():
    y = os.popen('ps axu|grep logstash|grep conf|grep -v ps|awk \'{print $1}\'')
    if not y.read():
        os.popen('cd /usr/local/src/logstash-6.2.4; ./bin/logstash -f config/logstash.conf 2>&1 &')

if __name__ == "__main__":
    # for i in range(100):
        monitor_mongo()
        # monitor_logstash()
    #rem()
