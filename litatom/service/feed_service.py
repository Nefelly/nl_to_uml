# coding: utf-8
import time
import random
import datetime
from ..redis import RedisClient
from ..key import (
    REDIS_FEED_SQUARE
)
from ..util import (
    get_time_info,
)
from ..const import (
    MAX_TIME
)

from ..service import (
    UserService,
    BlockService
)
from ..model import (
    Feed,
    FeedLike,
    FeedComment,
    UserMessage
)

redis_client = RedisClient()['lit']

class FeedService(object):

    @classmethod
    def _feed_info(cls, feed, visitor_user_id=None):
        if not feed:
            return {}
        user_info = UserService.user_info_by_uid(feed.user_id)
        res = feed.get_info()
        res['user_info'] = user_info
        if visitor_user_id:
            res['liked'] = True if FeedLike.get_by_ids(visitor_user_id, str(feed.id)) else False
        return res

    @classmethod
    def _add_to_feed_pool(cls, feed):
        redis_client.zadd(REDIS_FEED_SQUARE, {str(feed.id): feed.create_time})

    @classmethod
    def _del_from_feed_pool(cls, feed):
        redis_client.zrem(REDIS_FEED_SQUARE, str(feed.id))

    @classmethod
    def create_feed(cls, user_id, content, pics=None):
        feed = Feed.create_feed(user_id, content, pics)
        cls._add_to_feed_pool(feed)
        return str(feed.id)

    @classmethod
    def delete_feed(cls, user_id, feed_id):
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return None, True
        if not feed.user_id != user_id:
            return u'you are not authorized', False
        cls._del_from_feed_pool(feed)
        FeedLike.objects(feed_id=feed_id).delete()
        FeedComment.objects(feed_id=feed_id).delete()
        feed.delete()

    @classmethod
    def feeds_by_userid(cls, visitor_user_id, user_id, start_ts=MAX_TIME, num=10):
        msg = BlockService.get_block_msg(visitor_user_id, user_id)
        if msg:
            return msg, False
        if start_ts < 0:
            return u'wrong start_ts', False
        next_start = -1
        feeds = Feed.objects(user_id=user_id, create_time__lte=start_ts).limit(num + 1)
        feeds = list(feeds)
        feeds.reverse()   # 时间顺序错误
        has_next = False
        if len(feeds) == num + 1:
            has_next = True
            next_start = feeds[-1].create_time
            feeds = feeds[:-1]
        return {
            'feeds': map(cls._feed_info, feeds, [visitor_user_id for el in feeds]),
            'has_next': has_next,
            'next_start': next_start
        }, True

    @classmethod
    def feeds_by_square(cls, user_id, start_p=0, num=10):
        feeds = redis_client.zrevrange(REDIS_FEED_SQUARE, start_p, start_p + num)
        feeds = map(Feed.get_by_id, feeds) if feeds else []
        has_next = False
        if len(feeds) == num + 1:
            has_next = True
            feeds = feeds[:-1]
        feeds = map(cls._feed_info, feeds, [user_id for el in feeds])
        return {
            'has_next': has_next,
            'feeds': feeds,
            'next_start': start_p + num if has_next else -1
        }
        
    @classmethod
    def like_feed(cls, user_id, feed_id):
        like_now = FeedLike.reverse(user_id, feed_id)
        num = 1 if like_now else -1
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return 'wrong feed id', False
        feed.chg_feed_num(num)
        UserMessage.add_message(feed.user_id, user_id, UserMessage.MSG_LIKE, feed_id)
        return {'like_now': like_now}, True

    @classmethod
    def comment_feed(cls, user_id, feed_id, content, comment_id=None):
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return u'wrong feedid', False
        comment = FeedComment()
        if comment_id:
            father_comment = FeedComment.get_by_id(comment_id)
            if not father_comment:
                return u'comment of id:%s not exists' % comment_id, False
            if father_comment.user_id == user_id:
                return u'could not comment on yourself\'s comement', False
            if father_comment.comment_id:   # 直接评论到一级目录里  不支持多级嵌套
                comment_id = father_comment.comment_id
            comment.comment_id = comment_id
            comment.content_user_id = father_comment.user_id
            UserMessage.add_message(father_comment.user_id, user_id, UserMessage.MSG_COMMENT, feed_id, content)
        else:
            UserMessage.add_message(feed.user_id, user_id, UserMessage.MSG_REPLY, feed_id, content)
        feed.chg_comment_num(1)
        comment.user_id = user_id
        comment.feed_id = feed_id
        comment.content = content
        comment.create_time = int(time.time())
        comment.save()
        return {'comment_id': str(comment.id)}, True

    @classmethod
    def get_feed_comments(cls, user_id, feed_id):
        comments = FeedComment.get_by_feed_id(feed_id)
        comments = list(comments)
        user_ids = [obj.user_id for obj in comments]
        user_info_m = UserService.batch_get_user_info_m(user_ids)
        res = []
        ind = 0
        comment_id_index = {}
        for c in comments:
            if not c.comment_id:
                _ = {
                    'time_info': get_time_info(c.create_time),
                    'inner_comments': [],
                    'user_info': user_info_m.get(c.user_id, {}),
                    'content': c.content,
                    'comment_id': str(c.id)
                }
                res.append(_)
                comment_id_index[str(c.id)] = ind
                ind += 1
        for c in comments:
            if c.comment_id:
                tmp_ind = comment_id_index.get(c.comment_id)
                if not tmp_ind and tmp_ind != 0:
                    c.delete()
                    c.save()
                    continue
                _ = {
                    'time_info': get_time_info(c.create_time),
                    'user_info': user_info_m.get(c.user_id, {}),
                    'content': c.content,
                    'comment_id': str(c.id),
                    'content_user_id': c.content_user_id
                }
                res[tmp_ind]['inner_comments'].append(_)
        return res, True
