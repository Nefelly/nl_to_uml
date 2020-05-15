# coding: utf-8
import json
import time
import traceback
import logging
from ..model import (
    VisitRecord,
    NewVisit,
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


    @classmethod
    def visit(cls, user_id, other_user_id):
        VisitRecord.add_visit(user_id, other_user_id)
        NewVisit.incr_visited(other_user_id)
        return None, True

    @classmethod
    def new_visited_num(cls, user_id):
        num = NewVisit.new_viewed_num()
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
            for i in range(len(res)):
                user_id = res[i]['user_id']
                res[i]['user_info'] = user_info_m.get(user_id, {})
        return {'records': res}, True

    @classmethod
    def all_viewed(cls, user_id):
        NewVisit.record_has_viewed(user_id)
        redis_client.set(cls.new_visited_cache_key(user_id), 0, cls.VISITED_CACHE_TIME)
        return None, True

    @classmethod
    def test_env_set(cls):
        if not setting.IS_DEV:
            return False
        visited = User.get_by_phone('8618938951380')
        visited_id = str(visited.id)
        print visited.session
        for _ in UserService.get_all_ids():
            if _:
                cls.visit(_, visited_id)