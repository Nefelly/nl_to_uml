# coding: utf-8
import json
import time
import traceback
import logging
from ..model import (
    VisitRecord,
    DiffVisitRecord
)
from ..key import (
    REDIS_NEW_VISIT_NUM
)
from ..service import (
    AccountService,
    UserService
)
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
        pass

    @classmethod
    def new_visited_num(cls, user_id):
        num = redis_client.get(REDIS_NEW_VISIT_NUM.format(user_id=user_id))
        if num:
            num = int(num)
        else:
            total_num = sum([el.visit_num for el in VisitRecord.objects(target_user_id=user_id)])

        num = 0 if not num else int(num)
        pass

    @classmethod
    def get_visited_list(cls, user_id, page_num, num):
        pass

    @classmethod
    def all_visited(cls, user_id):
        pass