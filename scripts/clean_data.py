import os
from litatom.model import *
from litatom.redis import RedisClient
from litatom.service import UserService
import datetime
import time

redis_client = RedisClient()['lit']

def clear_redis():
    for k in redis_client.keys():
        redis_client.delete(k)

def clear_by_date():
    time.mktime(time.strptime("2019-11-02 00:00:00","%Y-%m-%d %H:%M:%S"))
    a = datetime.datetime(2019, 4,2, 0, 0 ,0)
    ls = User.objects(create_time__lte=a)
    ls = list(ls)
    map(UserService._delete_user, ls)

def clear_feeds():
    a = time.mktime(time.strptime("2019-11-02 00:00:00","%Y-%m-%d %H:%M:%S"))
    ls = redis_client.zrangebyscore('feed_square', 0, a)
    def r(fid):
        redis_client.zrem('feed_square', fid)
        Feed.get_by_id(fid).delete()
    map(r, ls)

def clear_objs():
    map(UserService._delete_user, User.objects())
    for cls in [Blocked, Feed, FeedLike, FeedComment, Follow, Report, Feedback,
                UserAction, UserRecord, UserMessage]:
        cls.objects().delete()

if __name__ == '__main__':
    if os.getcwd().split('/')[-1] != 'devlitatom':
        print 'not right path'
        assert False
        exit()
    exit()
    assert False
    clear_objs()
    clear_redis()