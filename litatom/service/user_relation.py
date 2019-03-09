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
    DEFAULT_QUERY_LIMIT
)
from ..service import (
    HuanxinService
)

class FollowService(object):

    @classmethod
    def follow(cls, user_id, followed_user_id):
        block_msg = BlockService.get_block_msg(user_id, followed_user_id)
        if block_msg:
            return block_msg, False
        Follow.follow(user_id, followed_user_id)
        if Follow.get_by_follow(followed_user_id, user_id):
            user_huanxin = User.huanxin_id_by_user_id(user_id)
            followed_huanxin = User.huanxin_id_by_user_id(followed_user_id)
            if user_huanxin and followed_huanxin:
                HuanxinService.add_friend(user_huanxin, followed_huanxin)
                HuanxinService.add_friend(followed_huanxin, user_huanxin)
        return None, True

    @classmethod
    def unfollow(cls, user_id, followed_user_id):
        Follow.unfollow(user_id, followed_user_id)
        return None, True

    @classmethod
    def follow_eachother(cls, uid1, uid2):
        block_msg = BlockService.get_block_msg(uid1, uid2)
        if block_msg:
            return block_msg, False
        Follow.follow(uid1, uid2)
        Follow.follow(uid2, uid1)
        user_huanxin = User.huanxin_id_by_user_id(uid1)
        followed_huanxin = User.huanxin_id_by_user_id(uid2)
        if user_huanxin and followed_huanxin:
            HuanxinService.add_friend(user_huanxin, followed_huanxin)
            HuanxinService.add_friend(followed_huanxin, user_huanxin)
        return None, True

    @classmethod
    def unfollow_eachother(cls, uid1, uid2):
        Follow.unfollow(uid1, uid2)
        Follow.unfollow(uid2, uid1)
        return None, True

    @classmethod
    def follows(cls, user_id):
        follow_uids = [obj.followed for obj in Follow.objects(uid=user_id).limit(DEFAULT_QUERY_LIMIT)]
        users = map(User.get_by_id, follow_uids)
        return [u.basic_info() for u in users if u], True
    

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
    def blokeds(cls, user_id):
        blocked_uids = [obj.bloked for obj in Blocked.objects(uid=user_id).limit(DEFAULT_QUERY_LIMIT)]
        users = map(User.get_by_id, blocked_uids)
        return [u.basic_info() for u in users if u], True