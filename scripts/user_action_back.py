import os
import time
import datetime
from litatom.service import ChatRecordService

keep_time = 8 * 3600 * 24
save_dir = '/data/chats'

def back():
    host = ''
    port = 27017
    user =
    pwd =
    query_time = int(time.time()) - keep_time
    save_add = "%s/%s" % (save_dir, (datetime.datetime.now() - datetime.timedelta(days=1)).strftime('%Y-%m-%d'))
    sql = '''mongoexport -h %s --port %r -u %s -p %s --authenticationDatabase lit -d lit -c user_action -o %s -q '{"create_time": {$lt:%s}}}''' % (host, port, user, pwd, save_add, query_time)
    os.system(sql)


def ensure_path(path):
    dir_name  = path[:path.rfind('/')]
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)

def clean_old_records():
    time_now = int(time.time())
    HuanxinMessage.objects(create_time__lt=(time_now - keep_time))

def insert_records():
    time_now = time.time()
    two_hour_ago = ChatRecordService.get_hour_str(time_now - 2 * 3600)
    content = ChatRecordService.get_source_content(two_hour_ago)
    path = os.path.join(save_dir, '%s/%s.txt'% (two_hour_ago[:6], two_hour_ago))
    ensure_path(path)
    if os.path.exists(path):
        return
    with open(path, 'w') as f:
        f.write(content)
        f.close()
    msgs = ChatRecordService.records_by_content(content)
    for msg in msgs:
        try:
            ChatRecordService.save_to_db(msg)
        except Exception as e:
            print e
            continue


if __name__ == "__main__":
    print "started at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    clean_old_records()
    insert_records()
    print "ended at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
