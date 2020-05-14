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
            feeds = Feed.objects()
        elif condition == cls.FEED_RECOMMENDED:

        elif condition == cls.FEED_USER_UNRELIABLE:

        else:
            return 'invalid condition', False
