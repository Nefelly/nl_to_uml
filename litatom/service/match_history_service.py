# coding: utf-8
import json
import time
import traceback
import cPickle
import logging
from ..model import (
    MatchRecord,
    MatchHistory,
)
from ..service import (
    UserService,
    MqService
)
from ..const import (
    ONE_DAY,
    USER_MODEL_EXCHANGE
)
from hendrix.conf import setting
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class MatchHistoryService(object):
    '''
    后续得做成批量的 难设计
    用户访问记录  v3.5
    查看差值时： 先命中缓存， 缓存有就从缓存取； 无： 就从库里取 差值； 在访问完成后就去除缓存， 设置库里的值为现有的值
    '''

    @classmethod
    def get_match_history(cls, user_id, page_num, num):
        objs = MatchHistory.get_by_user_id(user_id, page_num, num)
        res = []
        for obj in objs:
            res.append(obj.to_json())
        # if AccountService.is_member(user_id):
        if True:
            user_ids = [el.other_user_id for el in objs]
            user_info_m = UserService.batch_get_user_info_m(user_ids)
            for i in range(len(res)):
                user_id = res[i]['other_user_id']
                res[i]['user_info'] = user_info_m.get(user_id, {})
        return {'records': res}, True

    @classmethod
    def add_match_record(cls, user_id1, user_id2, match_type, quit_user, match_time, inter_time, is_friend=None):
        obj = MatchRecord.create(user_id1, user_id2, match_type, quit_user, match_time,
                                 inter_time)
        MqService.push(USER_MODEL_EXCHANGE, {'model_type': 'match', 'data': str(cPickle.dumps(obj))})
        MatchHistory.add_match(user_id1, user_id2, match_time, inter_time, is_friend)
        MatchHistory.add_match(user_id2, user_id1, match_time, inter_time, is_friend)
        return None, True

    @classmethod
    def send_add_request(cls, user_id, other_user_id, match_success_time):
        obj = MatchHistory.get_specified(user_id, other_user_id, match_success_time)
        other_obj = MatchHistory.get_specified(other_user_id, user_id, match_success_time)
        print obj, '!!!', other_obj
        if not obj or not other_obj:
            return u'fake match record', False
        if obj.friend_status == MatchHistory.STRANGER:
            obj.friend_status = MatchHistory.SEND_REQUEST
            obj.save()
        elif obj.friend_status == MatchHistory.WAIT_TO_ACCEPT:
            obj.friend_status = MatchHistory.FRIENDS
            obj.save()
        if other_obj.friend_status == MatchHistory.SEND_REQUEST:
            other_obj.friend_status == MatchHistory.FRIENDS
            other_obj.save()
        else:
            other_obj.friend_status == MatchHistory.WAIT_TO_ACCEPT
            other_obj.save()
        return None, True
        # elif obj.friend_status == cls.WAIT_TO_ACCEPT:
        #     obj.friend_status = cls.FRIENDS

    @classmethod
    def accept_friend_request(cls, user_id, other_user_id, match_success_time):
        obj = MatchHistory.get_specified(user_id, other_user_id, match_success_time)
        other_obj = MatchHistory.get_specified(other_user_id, user_id, match_success_time)
        if not obj or not other_obj:
            return u'fake match record', False
        if other_obj.friend_status != MatchHistory.SEND_REQUEST:
            return u'other party has not send you add request', False
        if not obj.friend_status == MatchHistory.WAIT_TO_ACCEPT:
            return u'you are in wrong states', False
        obj.friend_status = MatchHistory.FRIENDS
        other_obj.friend_status = MatchHistory.FRIENDS
        obj.save()
        other_obj.save()
        return None, True

    @classmethod
    def test_env_set(cls):
        from hendrix.conf import setting
        if not setting.IS_DEV:
            return False
        from ..model import User
        test_user = User.get_by_phone('8618938951380')
        test_user_id = str(test_user.id)
        print test_user.session, test_user_id
        import random
        for _ in UserService.get_all_ids():
            if _:
                r = random.randint(1, 1000)
                cls.add_match_record(test_user_id, _, 'anoy1', _, int(time.time()) + r, r % 10, r % 4 == 0)

