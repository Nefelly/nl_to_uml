# coding: utf-8
import time
import random
import datetime
from hendrix.conf import setting
from flask import (
    request
)

from ..redis import RedisClient
from ..key import (
    REDIS_FEED_SQUARE_REGION,
    REDIS_FEED_HQ_REGION,
    REDIS_FEED_ID_AGE,
    REDIS_REGION_FEED_TOP
)
from ..util import (
    get_time_info,
)
from ..const import (
    MAX_TIME,
    ONE_DAY,
    REMOVE_EXCHANGE,
    ADD_EXCHANGE,
    ONE_HOUR,
    ONE_MIN,
    BLOCK_PIC,
    REVIEW_PIC, FEED_NEED_CHECK
)

from ..service import (
    UserService,
    UserModelService,
    BlockService,
    Ip2AddressService,
    UserMessageService,
    FollowingFeedService,
    GlobalizationService,
    UserMessageService,
    MqService,
    ForbidActionService,
    AntiSpamRateService,
    SpamWordCheckService,
    ForbidCheckService
)
from ..model import (
    Feed,
    FeedLike,
    FeedDislike,
    FeedComment,
    UserSetting
)

redis_client = RedisClient()['lit']


class FeedService(object):
    LATEST_TYPE = 'latest'
    COMMENT_MAX_LEN = 500

    @classmethod
    def should_add_to_square(cls, feed):
        # return True
        user_id = feed.user_id
        judge_time = int(time.time()) - 5 * ONE_MIN
        if feed.self_high:
            return False
        status = Feed.objects(user_id=user_id, create_time__gte=judge_time).count() <= 3
        # if not status and setting.IS_DEV:
        if status:
            return True
        AntiSpamRateService.inform_spam(user_id, 'feed_over')
        return status

    @classmethod
    def pin_feed(cls, user_id, feed_id):
        user_setting = UserSetting.get_by_user_id(user_id)
        user_setting.pinned_feed = feed_id
        user_setting.save()
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return u'you should pin your own feed', False
        return None, True

    @classmethod
    def unpin_feed(cls, user_id, feed_id=None):
        user_setting = UserSetting.get_by_user_id(user_id)
        if not user_setting:
            return None, True
        if feed_id:
            if user_setting.pinned_feed != feed_id:
                return u'your unpin feed_id is not right', False
        user_setting.pinned_feed = ''
        user_setting.save()
        return None, True

    @classmethod
    def _on_add_feed(cls, feed):
        if not feed.pics:
            if cls.should_add_to_square(feed):
                cls._add_to_feed_pool(feed)
        MqService.push(ADD_EXCHANGE,
                       {"feed_id": str(feed.id), "pics": feed.pics,
                        "region_key": cls._redis_feed_region_key(REDIS_FEED_SQUARE_REGION)})
        # print 'push', {"feed_id": str(feed.id), "pics": feed.pics,
        #                 "region_key": cls._redis_feed_region_key(REDIS_FEED_SQUARE_REGION)}
        # FollowingFeedService.add_feed(feed)

    @classmethod
    def consume_feed_added(cls, feed_id, pics, region_key):
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return
        if pics:
            no_use, pic_res = ForbidCheckService.check_content(pics=pics)
            reviewed_tag = False
            for pic in pic_res:
                print(pic_res)
                if pic_res[pic][1] == BLOCK_PIC:
                    # TrackSpamRecordService.save_record(feed.user_id, pic=pic, forbid_weight=ForbidActionService.BLOCK_PIC_WEIGHTING)
                    GlobalizationService.set_current_region_for_script(GlobalizationService.get_region_by_user_id(feed.user_id))
                    ForbidActionService.resolve_block_pic(feed.user_id, pic)
                    FeedLike.del_by_feedid(feed_id)
                    FeedComment.objects(feed_id=feed_id).delete()
                    feed.delete()
                    return
                if not reviewed_tag and pic_res[pic][1] == REVIEW_PIC:
                    feed.status = FEED_NEED_CHECK
                    feed.save()
                    reviewed_tag = True

            #  need region to send to this because of request env
            if feed.pics and cls.should_add_to_square(feed):
                redis_client.zadd(region_key,{str(feed.id): feed.create_time})
        FollowingFeedService.add_feed(feed)

    @classmethod
    def consume_feed_removed(cls, feed_id):
        feed = Feed.get_by_id(feed_id)
        if feed:
            FollowingFeedService.remove_feed(feed)

    @classmethod
    def _on_del_feed(cls, feed):
        MqService.push(REMOVE_EXCHANGE, {"feed_id": str(feed.id)})
        # FollowingFeedService.remove_feed(feed)

    @classmethod
    def _redis_feed_region_key(cls, key):
        region = GlobalizationService.get_region()
        return key.format(region=region)

    @classmethod
    def _feed_info(cls, feed, visitor_user_id=None):
        if not feed:
            return {}
        if not feed.user_id:
            feed.delete()
            return {}
        user_info = UserService.user_info_by_uid(feed.user_id)
        res = feed.get_info()
        res['user_info'] = user_info
        if visitor_user_id:
            liked = False
            if feed.like_num:
                liked = FeedLike.in_like(visitor_user_id, str(feed.id), feed.like_num)
            res['liked'] = liked

            disliked = False
            if feed.dislike_num:
                disliked = FeedDislike.in_dislike(visitor_user_id, str(feed.id), feed.dislike_num)
            res['disliked'] = disliked
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
    def _add_to_feed_pool(cls, feed):
        redis_client.zadd(cls._redis_feed_region_key(REDIS_FEED_SQUARE_REGION), {str(feed.id): feed.create_time})

    @classmethod
    def _del_from_feed_pool(cls, feed):
        redis_client.zrem(cls._redis_feed_region_key(REDIS_FEED_SQUARE_REGION), str(feed.id))

    @classmethod
    def _add_to_feed_hq(cls, feed_id):
        redis_client.zadd(cls._redis_feed_region_key(REDIS_FEED_HQ_REGION), {feed_id: int(time.time())})

    @classmethod
    def add_hq(cls, feed_id):
        cls._add_to_feed_hq(feed_id)
        return None, True

    @classmethod
    def remove_from_hq(cls, feed_id):
        redis_client.zrem(cls._redis_feed_region_key(REDIS_FEED_HQ_REGION), feed_id)
        return None, True

    @classmethod
    def _del_from_feed_hq(cls, feed):
        redis_client.zrem(cls._redis_feed_region_key(REDIS_FEED_HQ_REGION), str(feed.id))

    @classmethod
    def judge_add_to_feed_hq(cls, feed):
        if feed and feed.is_hq:
            time_now = int(time.time())
            if time_now - feed.create_time >= 2 * ONE_DAY:
                return
            if not feed.self_high and not AntiSpamRateService.is_spamed_recent(feed.user_id):
                cls._add_to_feed_hq(str(feed.id))

    @classmethod
    def remove_from_pub(cls, feed):
        back_region = request.region
        request.region = GlobalizationService.get_region_by_user_id(feed.user_id)
        cls._del_from_feed_pool(feed)
        cls._del_from_feed_hq(feed)
        request.region = back_region
        if feed.should_remove_from_follow:
            MqService.push(REMOVE_EXCHANGE, {"feed_id": str(feed.id)})
            # FollowingFeedService.remove_feed(feed)

    @classmethod
    def move_up_feed(cls, feed_id, ts):
        return True
        # score = redis_client.zscore(REDIS_FEED_SQUARE, feed_id)
        # if score > 0:
        #     new_score = score + ts
        #     max_ts = int(time.time()) + 50
        #     if new_score > max_ts:
        #         new_score = max_ts
        #     redis_client.zadd(REDIS_FEED_SQUARE, {feed_id: new_score})

    @classmethod
    def create_feed(cls, user_id, content, pics=None, audios=None):
        if content:
            if SpamWordCheckService.is_spam_word(content):
                ForbidActionService.resolve_spam_word(user_id, content)
                return GlobalizationService.get_region_word('alert_msg'), False
        feed = Feed.create_feed(user_id, content, pics, audios)
        cls._on_add_feed(feed)
        UserModelService.add_comments_by_uid(user_id)
        # cls._add_to_feed_pool(feed)
        return str(feed.id), True

    @classmethod
    def delete_feed(cls, user_id, feed_id):
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return None, True
        if not getattr(request, 'is_admin', False) and feed.user_id != user_id:
            # if not request.is_admin and feed.user_id != user_id:
            return u'you are not authorized', False
        cls._del_from_feed_pool(feed)
        cls._del_from_feed_hq(feed)
        FeedLike.del_by_feedid(feed_id)
        FeedDislike.del_by_feedid(feed_id)
        FeedComment.objects(feed_id=feed_id).delete()
        feed.delete()
        MqService.push(REMOVE_EXCHANGE, {"feed_id": feed_id})
        return None, True

    @classmethod
    def get_pinned_feed(cls, user_id):
        user_setting = UserSetting.get_by_user_id(user_id)
        if user_setting and user_setting.pinned_feed:
            return Feed.get_by_id(user_setting.pinned_feed)
        return None

    @classmethod
    def feeds_by_userid(cls, visitor_user_id, user_id, start_ts=MAX_TIME, num=10):
        if request.ip_should_filter:
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
        feeds = Feed.objects(user_id=user_id, create_time__lte=start_ts).order_by('-create_time').limit(num + 1)
        feeds = list(feeds)
        if visitor_user_id != user_id:
            feeds = [el for el in feeds if not el.should_remove_from_follow]
        # feeds.reverse()   # 时间顺序错误
        has_next = False
        if len(feeds) == num + 1:
            has_next = True
            next_start = feeds[-1].create_time
            feeds = feeds[:-1]
        res = {
            'feeds': map(cls._feed_info, feeds, [visitor_user_id for el in feeds]),
            'has_next': has_next,
            'next_start': next_start
        }
        if start_ts >= MAX_TIME:
            pinned_feed_info = {}
            pinned_feed = cls.get_pinned_feed(user_id)
            ''' 自high的不能置顶'''
            if pinned_feed and not pinned_feed.should_remove_from_follow:
                pinned_feed_info = cls._feed_info(pinned_feed, visitor_user_id)
            if pinned_feed_info:
                res['pinned'] = pinned_feed_info
        return res, True

    @classmethod
    def _feeds_by_pool(cls, redis_key, user_id, start_p, num, pool_type=None):
        if request.ip_should_filter:
            return {
                'feeds': [],
                'has_next': False,
                'next_start': -1
            }

        feeds = []
        max_loop_tms = 5
        has_next = False
        next_start = -1
        top_id = None
        if start_p == 0 and pool_type == cls.LATEST_TYPE:
            top_id = redis_client.get(REDIS_REGION_FEED_TOP.format(region=GlobalizationService.get_region()))
        for i in range(max_loop_tms):
            tmp_feeds = redis_client.zrevrange(redis_key, start_p, start_p + num)
            has_next = False
            if len(tmp_feeds) == num + 1:
                has_next = True
                tmp_feeds = tmp_feeds[:-1]
            next_start = start_p + num if has_next else -1
            feeds += [el for el in tmp_feeds if UserService.age_in_user_range(user_id, cls.age_by_feed_id(el))]
            if len(feeds) >= max(num - 3, 1) or not has_next:
                break
            start_p = start_p + num
        if top_id:
            feeds = [top_id] + [el for el in feeds if el != top_id]
        feeds = map(Feed.get_by_id, feeds) if feeds else []
        feeds = [el for el in feeds if el and not FeedDislike.in_dislike(user_id, str(el.id), el.dislike_num)]
        feeds = map(cls._feed_info, feeds, [user_id for el in feeds])
        return {
            'has_next': has_next,
            'feeds': feeds,
            'next_start': next_start
        }

    @classmethod
    def feeds_by_square(cls, user_id, start_p=0, num=10):
        return cls._feeds_by_pool(cls._redis_feed_region_key(REDIS_FEED_SQUARE_REGION), user_id, start_p, num,
                                  cls.LATEST_TYPE)

    @classmethod
    def age_by_feed_id(cls, feed_id):
        key = REDIS_FEED_ID_AGE.format(feed_id=feed_id)
        age = redis_client.get(key)
        if age:
            return int(age)
        age = 0
        feed = Feed.get_by_id(feed_id)
        if feed:
            age = UserService.uid_age(feed.user_id)
        redis_client.set(key, age, ONE_DAY)
        return age

    @classmethod
    def feeds_square_for_admin(cls, user_id, start_p=0, num=10):
        res = cls.feeds_by_square(user_id, start_p, num)
        for feed in res['feeds']:
            if feed:
                feed.update(in_hq=cls._in_hq(feed['id']))
        return res

    @classmethod
    def _in_hq(cls, feed_id):
        return redis_client.zscore(cls._redis_feed_region_key(REDIS_FEED_HQ_REGION), feed_id) > 0

    @classmethod
    def feeds_by_hq(cls, user_id, start_p=0, num=10):
        return cls._feeds_by_pool(cls._redis_feed_region_key(REDIS_FEED_HQ_REGION), user_id, start_p, num)

    @classmethod
    def like_feed(cls, user_id, feed_id):
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return 'wrong feed id', False
        like_now = FeedLike.reverse(user_id, feed_id, feed.like_num)
        num = 1 if like_now else -1
        msg = BlockService.get_block_msg(feed.user_id, user_id)
        if msg:
            return msg, False
        feed.chg_feed_num(num)
        if feed.user_id != user_id and 1:
            chg_ts = 600
            if not like_now:
                chg_ts = -chg_ts
            cls.move_up_feed(feed_id, chg_ts)
            if like_now:
                cls.judge_add_to_feed_hq(feed)
                UserMessageService.add_message(feed.user_id, user_id, UserMessageService.MSG_LIKE, feed_id)
        return {'like_now': like_now}, True

    @classmethod
    def dislike_feed(cls, user_id, feed_id, reverse=True):
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return 'wrong feed id', False
        if feed.user_id == user_id:
            return u'you can\'t dislike yourself.', False
        num = 1
        if not reverse:
            is_dislike = FeedDislike.in_dislike(user_id, feed_id, feed.dislike_num)
            if is_dislike:
                return None, True
            is_dislike = FeedDislike.reverse(user_id, feed_id, feed.dislike_num)
        else:
            is_dislike = FeedDislike.reverse(user_id, feed_id, feed.dislike_num)
            num = 1 if is_dislike else -1
        feed.chg_dislike_num(num)
        if feed.user_id != user_id:
            if is_dislike:
                if feed.self_high:
                    cls.remove_from_pub(feed)
        return {'dislike_now': is_dislike}, True

    @classmethod
    def comment_feed(cls, user_id, feed_id, content, comment_id=None):
        feed = Feed.get_by_id(feed_id)
        if not feed:
            return u'wrong feedid', False
        if len(content) > cls.COMMENT_MAX_LEN:
            return u'your comment is too long', False
        msg = BlockService.get_block_msg(feed.user_id, user_id)
        if msg:
            return msg, False
        comment = FeedComment()
        tag = False
        if comment_id:
            father_comment = FeedComment.get_by_id(comment_id)
            if not father_comment:
                return u'comment of id:%s not exists' % comment_id, False
            # if father_comment.user_id == user_id:
            #     return u'could not comment on yourself\'s comement', False
            # 如果father comment也是一个评论回复，即father comment 也有father comment,就把当前评论的father comment设为根评论
            if father_comment.comment_id:  # 直接评论到一级目录里  不支持多级嵌套
                comment_id = father_comment.comment_id
            # 如果father comment不是一个评论回复，即为一个根评论，找到father comment的user_id，对评论回复力进行计数
            else:
                UserModelService.add_comments_replies_by_uid(father_comment.user_id)
            comment.comment_id = comment_id
            comment.content_user_id = father_comment.user_id
            tag = True
        # spam word comment will be stopped
        res = SpamWordCheckService.is_spam_word(content)
        if res:
            ForbidActionService.resolve_spam_word(user_id, content)
            return GlobalizationService.get_region_word('alert_msg'), False

        if feed.user_id != user_id:
            data, status = AntiSpamRateService.judge_stop(user_id, AntiSpamRateService.COMMENT, feed_id,
                                                          related_protcted=True)
            if not status:
                return data, False

        if tag:
            UserMessageService.add_message(father_comment.user_id, user_id, UserMessageService.MSG_COMMENT, feed_id,
                                           content)
        else:
            UserMessageService.add_message(feed.user_id, user_id, UserMessageService.MSG_REPLY, feed_id, content)
        feed.chg_comment_num(1)
        if user_id != feed.user_id:
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
        if not comment:
            return u'comment not exists', False
        feed = Feed.get_by_id(comment.feed_id)
        if not comment or not feed or (user_id not in [comment.user_id, feed.user_id]):
            return u'not authorized', False
        # todo 嵌套查找
        num = 1
        if not comment.comment_id:  # has not father comment
            num += FeedComment.objects(comment_id=comment_id).delete()  # delete son comments
        # feed = Feed.get_by_id(comment.feed_id)
        feed.chg_comment_num(-num)
        comment.delete()
        comment.save()
        return None, True

    @classmethod
    def get_feed_comments(cls, user_id, feed_id):
        feed = Feed.get_by_id(feed_id)
        unlimited = False
        if feed and feed.user_id == user_id:
            unlimited = True
        comments = FeedComment.get_by_feed_id(feed_id, unlimited)
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

    @classmethod
    def get_review_feed(cls, num=10000):
        feeds = Feed.get_review_feed(num)
        res = []
        for feed in feeds:
            temp = {'feed_id':feed.id, 'pics':feed.pics}
            res.append(temp)
        return res
