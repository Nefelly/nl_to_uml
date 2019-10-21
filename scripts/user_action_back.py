import os
import time
import datetime
from hendrix.conf import setting
from litatom.service import ChatRecordService

keep_time = 8 * 3600 * 24
save_dir = '/data/mongoback/user_action'

def ensure_path(path):
    dir_name = path[:path.rfind('/')]
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

def back():
    db_m = setting.DB_SETTINGS.get('DB_LIT')
    ''''host': u'mongodb://ll:11@172.31.138.46/lit?authsource=lit','''
    port = db_m['port']
    conn_url = db_m['host']
    user_pwd = conn_url.split('://')[1].split('@')[0]
    user, pwd = user_pwd.split(':')
    host = conn_url.split('@')[1].split('/')[0]
    query_time = int(time.time()) - keep_time
    save_add = "%s/%s" % (save_dir, (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'))
    ensure_path(save_add)
    sql = '''mongoexport -h %s --port %r -u %s -p %s --authenticationDatabase lit -d lit -c user_action -o %s -q '{"create_time": {$lt:%s}}\'''' % (host, port, user, pwd, save_add, query_time)
    print sql
    # os.popen(sql)


def clean_old_records():
    time_now = int(time.time())



if __name__ == "__main__":
    print "started at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    back()
    print "ended at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
