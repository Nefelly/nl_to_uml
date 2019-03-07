# coding: utf-8
import time
import random
import datetime
from ..redis import RedisClient
from ..key import (

)
from ..util import (
    now_date_key,
    low_high_pair
)
from ..const import (
    CREATE_HUANXIN_ERROR,
    ONE_DAY,
    FIVE_MINS,
    BOY,
    GIRL,
    MAX_TIME,
    USER_NOT_EXISTS,
    PROFILE_NOT_COMPLETE
)
from ..service import (
    UserService,
    FollowService,
    HuanxinService
)
from ..model import (
    Feed,
    FeedLike,
    FeedComment
)

redis_client = RedisClient()['lit']

class FeedService(object):

    @classmethod
    def feed_num(cls, user_id):
        return Feed.objects(user_id=user_id).count()

    @classmethod
    def feed_info(cls, user_id, feed):
        if not feed:
            return {}
        return feed.get_info()

    @classmethod
    def create_feed(cls, user_id, words, pics):
        Feed.create_feed(user_id, words, pics)

    @classmethod
    def feeds_by_userid(cls, user_id, start_id=0, num=10):
        User.objects(create_time__gte=datetime.datetime(2019, 3, 7, 15, 53, 22, 117000)).limit(5)

    @classmethod
    def feeds_by_gender(cls, user_id, gender):



    @classmethod
    def like_feed(cls, user_id, feed_id, start_pos=0, num=10):



    @classmethod
    def comment_feed(cls, user_id, feed_id, comment_id):


