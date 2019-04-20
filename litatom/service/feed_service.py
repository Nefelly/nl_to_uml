# coding: utf-8
import time
import random
import datetime
from  flask import (
    request
)
from ..redis import RedisClient
from ..key import (
    REDIS_FEED_SQUARE,
    REDIS_FEED_HQ
)
from ..util import (
    get_time_info,
)
from ..const import (
    MAX_TIME
)

from ..service import (
    UserService,
    BlockService,
    Ip2AddressService,
    UserMessageService
)
from ..model import (
    Feed,
    FeedLike,
    FeedComment
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
    def get_feed_info(cls, user_id, feed_id):
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return u'feed not exist!', False
        feed_info = cls._feed_info(feed, user_id)
        if not feed_info:
            return u'not feed info', False
        return feed_info, True


    @classmethod
    def _add_to_feed_pool(cls,  feed):
        redis_client.zadd(REDIS_FEED_SQUARE, {str(feed.id): feed.create_time})

    @classmethod
    def _del_from_feed_pool(cls,feed):
        redis_client.zrem( REDIS_FEED_SQUARE, str(feed.id))

    @classmethod
    def _add_to_feed_hq(cls, feed_id):
        redis_client.zadd(REDIS_FEED_HQ, {str(feed.id): int(time.time())})

    @classmethod
    def add_hq(cls, feed_id):
        cls._add_to_feed_hq(feed_id)
        return None, True

    @classmethod
    def remove_from_hq(cls, feed_id):
        redis_client.zrem( REDIS_FEED_HQ, feed_id)
        return None, True

    @classmethod
    def _del_from_feed_hq(cls, feed):
        redis_client.zrem( REDIS_FEED_HQ, str(feed.id))

    @classmethod
    def judge_add_to_feed_hq(cls, feed):
        if feed and feed.is_hq:
            cls._add_to_feed_hq(str(feed.id))

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
        if feed.user_id != user_id:
            return u'you are not authorized', False
        cls._del_from_feed_pool(feed)
        cls._del_from_feed_hq(feed)
        FeedLike.objects(feed_id=feed_id).delete()
        FeedComment.objects(feed_id=feed_id).delete()
        feed.delete()
        return None, True


    @classmethod
    def should_filter_ip(cls):
        if Ip2AddressService.ip_country(request.ip) in [u'United States']:
            return True
        return False

    @classmethod
    def feeds_by_userid(cls, visitor_user_id, user_id, start_ts=MAX_TIME, num=10):
        if cls.should_filter_ip():
            return {
                       'feeds': [],
                       'has_next': False,
                       'next_start': -1
            }, True
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
    def _feeds_by_pool(cls, redis_key, user_id, start_p, num):
        if cls.should_filter_ip():
            return {
                       'feeds': [],
                       'has_next': False,
                       'next_start': -1
                   }, True
        feeds = redis_client.zrevrange(redis_key, start_p, start_p + num)
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
    def feeds_by_square(cls, user_id, start_p=0, num=10):
        return cls._feeds_by_pool(REDIS_FEED_SQUARE, user_id, start_p, num)

    @classmethod
    def feeds_square_for_admin(cls, user_id, start_p=0, num=10):
        res = cls.feeds_by_square(user_id, start_p, num)
        for feed in res['feeds']:
            feed.update(in_hq=cls._in_hq(feed['feed_id']))
        return res

    @classmethod
    def _in_hq(cls, feed_id):
        return redis_client.zscore(REDIS_FEED_HQ, feed_id) > 0

    @classmethod
    def feeds_by_hq(cls, user_id, start_p=0, num=10):
        return cls._feeds_by_pool(REDIS_FEED_HQ, user_id, start_p, num)

    @classmethod
    def like_feed(cls, user_id, feed_id):
        like_now = FeedLike.reverse(user_id, feed_id)
        num = 1 if like_now else -1
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return 'wrong feed id', False
        feed.chg_feed_num(num)
        if like_now:
            cls.judge_add_to_feed_hq(feed)
            UserMessageService.add_message(feed.user_id, user_id, UserMessageService.MSG_LIKE, feed_id)
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
            UserMessageService.add_message(father_comment.user_id, user_id, UserMessageService.MSG_COMMENT, feed_id, content)
        else:
            UserMessageService.add_message(feed.user_id, user_id, UserMessageService.MSG_REPLY, feed_id, content)
        feed.chg_comment_num(1)
        cls.judge_add_to_feed_hq(feed)
        comment.user_id = user_id
        comment.feed_id = feed_id
        comment.content = content
        comment.create_time = int(time.time())
        comment.save()
        return {'comment_id': str(comment.id)}, True

    @classmethod
    def del_comment(cls, user_id, comment_id):
        comment = FeedComment.get_by_id(comment_id)
        if not comment or comment.user_id != user_id:
            return u'not authorized', False
        #todo  嵌套查找
        num = 1
        if not comment.comment_id:   # has not father comment
            num += FeedComment.objects(comment_id=comment_id).delete()   # delete son comments
        feed = Feed.get_by_id(comment.feed_id)
        feed.chg_comment_num(-num)
        comment.delete()
        comment.save()
        return None, True

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
