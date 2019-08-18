# coding: utf-8
import random
import time
import datetime
import ..model
from ..model import *
from ..service import (
    UserService,
    FirebaseService,
    FeedService
)
from ..const import (
    MAX_TIME
)
from ..redis import RedisClient

from ..key import (
    REDIS_USER_INFO_FINISHED,
    REDIS_ADMIN_USER
)

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']

class AdminService(object):
    UID_PWDS = {
        'joey': 'hypercycle'
    }

    @classmethod
    def c(cls):
        print dir(model)

