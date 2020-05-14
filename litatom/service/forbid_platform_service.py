from litatom.const import FEED_NEED_CHECK
from litatom.model import (
    Feed,
    UserSetting
)
from litatom.service import (
    ForbidActionService
)


class ForbidPlatformService(object):
    FEED_NEED_REVIEW = 'review'
    FEED_RECOMMENDED = 'recommended'
    FEED_USER_UNRELIABLE = 'score_up5'
    FEED_LOCATIONS = {'VN', 'TH', 'ID'}

    @classmethod
    def get_feed(cls, loc, condition):
        if loc not in cls.FEED_LOCATIONS:
            return 'invalid location', False
        if condition not in {cls.FEED_NEED_REVIEW, cls.FEED_RECOMMENDED, cls.FEED_USER_UNRELIABLE}:
            return 'invalid condition', False
        feeds = Feed.objects(status=FEED_NEED_CHECK).limit(100)
        res = []
        for feed in feeds:
            user_id = feed.user_id
            if loc and loc != UserSetting.get_loc_by_uid(user_id):
                continue
            is_hq = feed.is_hq
            if condition == cls.FEED_RECOMMENDED and not is_hq:
                continue
            forbid_score = ForbidActionService.accum_illegal_credit(user_id)
            if condition == cls.FEED_USER_UNRELIABLE and forbid_score <= 5:
                continue
            tmp = {'user_id': user_id, 'word': feed.content, 'pics': feed.pics, 'audio': feed.audios,
                   'comment_num': feed.comment_num, 'like_num': feed.like_num, 'hq': is_hq,
                   'forbid_score': forbid_score}
            res.append(tmp)
        return res, True
