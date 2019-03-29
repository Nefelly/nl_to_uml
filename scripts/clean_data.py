from litatom.model import *
from litatom.redis import RedisClient
from litatom.service import UserService

redis_client = RedisClient()['lit']

def clear_redis():
    for k in redis_client.keys():
        redis_client.delete(k)

def clear_objs():
    map(UserService._delete_user, User.objects())
    for cls in [Blocked, Feed, FeedLike, FeedComment, Follow, Report, Feedback,
                UserAction, UserRecord, UserMessage]:
        cls.objects().delete()

if __name__ == '__main__':
    clear_objs()
    clear_redis()