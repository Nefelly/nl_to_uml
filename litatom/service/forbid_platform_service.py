from litatom.const import FEED_NEED_CHECK
from litatom.model import (
    Feed,
    UserSetting
)


class ForbidPlatformService(object):
    FEED_NEED_REVIEW = 'review'
    FEED_RECOMMENDED = 'recommended'
    FEED_USER_UNRELIABLE = 'score_up5'
    FEED_LOCATIONS = {'VN','TH','ID'}


    @classmethod
    def get_feeed(cls, loc, condition):
        if loc not in cls.FEED_LOCATIONS:
            return 'invalid location', False
        if condition == cls.FEED_NEED_REVIEW:
            feeds = Feed.objects(status=FEED_NEED_CHECK).limit(100)
            res = []
            for feed in feeds:
                user_id = feed.user_id
                if loc:
                    UserSetting.get_loc_by_uid(user_id)
        elif condition == cls.FEED_RECOMMENDED:

        elif condition == cls.FEED_USER_UNRELIABLE:

        else:
            return 'invalid condition', False
