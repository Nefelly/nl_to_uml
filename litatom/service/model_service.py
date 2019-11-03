# coding: utf-8
import json
import time
import traceback
import logging
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']

class Service(object):
    '''
    docs :https://developer.qiniu.com/censor/api/5588/image-censor
    '''