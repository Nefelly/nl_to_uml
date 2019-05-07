# coding: utf-8
from  flask import (
    request
)
from ..const import (
    MAX_TIME
)
from ..model import (
    Feed,
    FollowingFeed,
    Follow
)


class FollowingFeedService(object):

    @classmethod
    def _add_following(cls, user_id, followed_user_id):
        for feed in Feed.get_by_user_id(followed_user_id):
            FollowingFeed.add_feed(user_id, feed)

    @classmethod
    def add_following(cls, user_id, followed_user_id):
        cls._add_following(user_id, followed_user_id)

    @classmethod
    def _remove_following(cls, user_id, followed_user_id):
        for feed in Feed.get_by_user_id(followed_user_id):
            FollowingFeed.delete_feed(user_id, feed)

    @classmethod
    def remove_following(cls, user_id, followed_user_id):
        cls._remove_following(user_id, followed_user_id)

    @classmethod
    def _user_ids_by_feed(cls, feed):
        feed_user_id = feed.user_id
        return Follow.follower_uids(feed_user_id)

    @classmethod
    def _add_feed(cls, feed):
        uids = cls._user_ids_by_feed(feed)
        uids.append(feed.user_id)
        for uid in uids:
            FollowingFeed.add_feed(uid, feed)

    @classmethod
    def add_feed(cls, feed):
        cls._add_feed(feed)

    @classmethod
    def _remove_feed(cls, feed):
        uids = cls._user_ids_by_feed(feed)
        uids.append(feed.user_id)
        for uid in uids:
            FollowingFeed.delete_feed(uid, feed)

    @classmethod
    def remove_feed(cls, feed):
        cls._remove_feed(feed)

    @classmethod
    def following_feeds_by_userid(cls, user_id, start_ts=MAX_TIME, num=10):
        if request.ip_should_filter:
            return {
                       'feeds': [],
                       'has_next': False,
                       'next_start': -1
            }, True
        if start_ts < 0:
            return u'wrong start_ts', False
        next_start = -1
        following_feeds = FollowingFeed.objects(user_id=user_id, feed_create_time__lte=start_ts).order_by('-feed_create_time').limit(num + 1)
        following_feeds = list(following_feeds)
        following_feeds.reverse()   # 时间顺序错误
        has_next = False
        if len(following_feeds) == num + 1:
            has_next = True
            next_start = following_feeds[-1].feed_create_time
            following_feeds = following_feeds[:-1]
        from ..service import FeedService
        feeds = []
        for following_feed in following_feeds:
            feed = Feed.get_by_id(following_feed.feed_id)
            if feed:
               feeds.append(FeedService._feed_info(feed, user_id))
            else:
                following_feed.delete()
                following_feed.save()
        return {
            'feeds': feeds,
            'has_next': has_next,
            'next_start': next_start
        }, True
