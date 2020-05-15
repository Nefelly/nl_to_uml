# coding: utf-8
import json
import time
import traceback
import logging
from ..model import (
    VisitRecord,
    HasViewedVisit,
    User
)
from ..key import (
    REDIS_NEW_VISIT_NUM
)
from ..service import (
    AccountService,
    UserService
)
from ..const import (
    ONE_DAY
)
from hendrix.conf import setting
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class VisitService(object):
    '''
    用户访问记录  v3.5
    查看差值时： 先命中缓存， 缓存有就从缓存取； 无： 就从库里取 差值； 在访问完成后就去除缓存， 设置库里的值为现有的值
    '''
    VISITED_CACHE_TIME = ONE_DAY
    @classmethod
    def new_visited_cache_key(cls, user_id):
        return REDIS_NEW_VISIT_NUM.format(user_id=user_id)

    @classmethod
    def visit(cls, user_id, other_user_id):
        VisitRecord.add_visit(user_id, other_user_id)
        redis_client.incr(cls.new_visited_cache_key(user_id))
        redis_client.expire(cls.new_visited_cache_key(user_id), cls.VISITED_CACHE_TIME)
        return None, True

    @classmethod
    def new_visited_num(cls, user_id):
        num = redis_client.get(cls.new_visited_cache_key(user_id))
        if num is not None:
            num = int(num)
        else:
            total_num = sum([el.visit_num for el in VisitRecord.objects(target_user_id=user_id)])
            has_viewed = HasViewedVisit.get_has_viewed_num(user_id)
            num = max(total_num - has_viewed, 0)
            redis_client.set(cls.new_visited_cache_key(user_id), num, cls.VISITED_CACHE_TIME)
        return {'num': num}, True

    @classmethod
    def get_visited_list(cls, user_id, page_num, num):
        objs = VisitRecord.get_by_target_user_id(user_id, page_num, num)
        is_member = AccountService.is_member(user_id)
        res = []
        for obj in objs:
            res.append(obj.to_json())
        if is_member:
            user_ids = [el.user_id for el in objs]
            user_info_m = UserService.batch_get_user_info_m(user_ids)
            for i in range(res):
                user_id = res[i]['user_id']
                res[i]['user_info'] =user_info_m.get(user_id, {})
        return {'records': res}, True

    @classmethod
    def all_viewed(cls, user_id, num):
        HasViewedVisit.record_has_viewed(user_id, num)
        redis_client.set(cls.new_visited_cache_key(user_id), cls.VISITED_CACHE_TIME)
        return None, True

    @classmethod
    def test_env_set(cls):
        if not setting.IS_DEV:
            return False
        visited = User.get_by_phone('8618938951380')
        visited_id = str(visited.id)
        print visited.session
        for _ in UserService.get_all_ids():
            cls.visit(_, visited_id)