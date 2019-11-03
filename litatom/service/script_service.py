# coding: utf-8
import random
import time
import datetime
from flask import (
    request
)
from mongoengine.queryset.visitor import Q
from collections import Counter
from ..model import (
    UserAction
)
from ..redis import RedisClient

from ..util import get_times_from_str, next_date, date_to_int_time

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']

def stat_distribute():
    start_d = get_times_from_str('20191102')[1]
    end_d = next_date(start_d)
    objs = UserAction.objects(action='match', create_time__gte=date_to_int_time(start_d),
                              create_time__lte=date_to_int_time(end_d), remark__contains='start')
    ucc = [el.user_id for el in objs]
    counts = Counter(ucc)
    uccc = [counts[el] for el in counts]
    uccc_counts = Counter(uccc)
    print uccc_counts
