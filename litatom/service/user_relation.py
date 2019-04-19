# coding: utf-8
from ..redis import RedisClient
from ..model import (
    Follow,
    Blocked,
    User
)
from ..const import (
    BLOCKED_MSG,
    BLOCK_OTHER_MSG,
    DEFAULT_QUERY_LIMIT,
    MAX_TIME
)
from ..service import (
    HuanxinService,
)

class FollowService(object):

    @classmethod
    def follow(cls, user_id, followed_user_id):
        block_msg = BlockService.get_block_msg(user_id, followed_user_id)
        if block_msg:
            return block_msg, False
        status = Follow.follow(user_id, followed_user_id)
        if status:
            User.chg_follower(followed_user_id, 1)
            User.chg_following(user_id, 1)
        if Follow.get_by_follow(followed_user_id, user_id):
            user_huanxin = User.huanxin_id_by_user_id(user_id)
            followed_huanxin = User.huanxin_id_by_user_id(followed_user_id)
            if user_huanxin and followed_huanxin:
                HuanxinService.add_friend(user_huanxin, followed_huanxin)
                HuanxinService.add_friend(followed_huanxin, user_huanxin)
        from ..service import UserMessageService
        UserMessageService.add_message(followed_user_id, user_id, UserMessageService.MSG_FOLLOW)
        return None, True

    @classmethod
    def unfollow(cls, user_id, followed_user_id):
        status = Follow.unfollow(user_id, followed_user_id)
        if status:
            User.chg_follower(followed_user_id, -1)
            User.chg_following(user_id, -1)
        return None, True

    @classmethod
    def follow_eachother(cls, uid1, uid2):
        block_msg = BlockService.get_block_msg(uid1, uid2)
        if block_msg:
            return block_msg, False
        status1 = Follow.follow(uid1, uid2)
        if status1:
            User.chg_follower(uid2, 1)
            User.chg_following(uid1, 1)
        status2 = Follow.follow(uid2, uid1)
        if status2:
            User.chg_follower(uid1, 1)
            User.chg_following(uid2, 1)
        user_huanxin = User.huanxin_id_by_user_id(uid1)
        followed_huanxin = User.huanxin_id_by_user_id(uid2)
        if user_huanxin and followed_huanxin:
            HuanxinService.add_friend(user_huanxin, followed_huanxin)
            HuanxinService.add_friend(followed_huanxin, user_huanxin)
        return None, True

    @classmethod
    def unfollow_eachother(cls, uid1, uid2):
        status1 = Follow.unfollow(uid1, uid2)
        if status1:
            User.chg_follower(uid2, -1)
            User.chg_following(uid1, -1)
        status2 = Follow.unfollow(uid2, uid1)
        if status2:
            User.chg_follower(uid1, -1)
            User.chg_following(uid2, -1)
        return None, True

    @classmethod
    def following(cls, user_id, start_ts=0, num=10):
        objs = Follow.objects(uid=user_id, create_time__gte=start_ts).limit(num + 1)
        objs = list(objs)
        has_next = False
        next_start = -1
        if len(objs) == num + 1:
            has_next = True
            next_start = objs[-1].create_time
            objs = objs[:-1]
        follow_uids = [obj.followed for obj in objs]
        users = map(User.get_by_id, follow_uids)
        res = {
            'has_next': has_next,
            'next_start': next_start,
            'users': [u.basic_info() for u in users if u]
        }
        return res, True

    @classmethod
    def follower(cls, user_id, start_ts=0, num=10):
        objs = Follow.objects(followed=user_id, create_time__gte=start_ts).limit(num + 1)
        objs = list(objs)
        has_next = False
        next_start = -1
        if len(objs) == num + 1:
            has_next = True
            next_start = objs[-1].create_time
            objs = objs[:-1]
        follow_uids = [obj.uid for obj in objs]
        users = map(User.get_by_id, follow_uids)
        res = {
            'has_next': has_next,
            'next_start': next_start,
            'users': [u.basic_info() for u in users if u]
        }
        return res, True
    

class BlockService(object):

    @classmethod
    def get_block_msg(cls, uid1, uid2):
        if not uid1 or not uid2:
            return None
        if Blocked.get_by_block(uid1, uid2):
            return BLOCK_OTHER_MSG
        if Blocked.get_by_block(uid2, uid1):
            return BLOCKED_MSG
        return None

    @classmethod
    def block(cls, uid, blocked_uid):
        FollowService.unfollow_eachother(uid, blocked_uid)
        Blocked.block(uid, blocked_uid)
        user_huanxin = User.huanxin_id_by_user_id(uid)
        blocked_huanxin = User.huanxin_id_by_user_id(blocked_uid)
        if user_huanxin and blocked_huanxin:
            HuanxinService.block_user(user_huanxin, blocked_huanxin)
            HuanxinService.block_user(blocked_huanxin, user_huanxin)
        return None, True
        
    @classmethod
    def unblock(cls, uid, blocked_uid):
        Blocked.unblock(uid, blocked_uid)
        if not Blocked.get_by_block(blocked_uid, uid):
            user_huanxin = User.huanxin_id_by_user_id(uid)
            blocked_huanxin = User.huanxin_id_by_user_id(blocked_uid)
            if user_huanxin and blocked_huanxin:
                HuanxinService.unblock_user(user_huanxin, blocked_huanxin)
                HuanxinService.unblock_user(blocked_huanxin, user_huanxin)
        return None, True

    @classmethod
    def blocks(cls, user_id):
        blocked_uids = [obj.blocked for obj in Blocked.objects(uid=user_id).limit(DEFAULT_QUERY_LIMIT)]
        users = map(User.get_by_id, blocked_uids)
        return [u.basic_info() for u in users if u], True