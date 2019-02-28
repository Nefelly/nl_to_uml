from __future__ import absolute_import

import logging

from hendrix.conf import setting
from redis import StrictRedis

from . import json
from .util import BaseDBManager

logger = logging.getLogger(__name__)


class RedisClient(BaseDBManager):
    @property
    def settings(self):
        return setting.REDIS_SETTINGS

    def _initdb(self, name):
        if 'url' in self.settings[name]:
            self[name] = StrictRedis.from_url(self.settings[name]['url'])
        else:
            self[name] = StrictRedis(**self.settings[name])


class RedisCacheUtils(object):

    @classmethod
    def get_or_set(cls, redis_client, cache_key, supplier, expire_time):
        """
        get string from redis and parse it as a json-serializable object (typically a dict/list)
        :param redis_client: instance of `StrictRedis`
        :param cache_key: string
        :param supplier: a callable used to generate desired result when cache missed
        :param expire_time: in seconds
        :return:
        """
        cached_str = redis_client.get(cache_key)
        if cached_str:
            return json.loads(cached_str)

        result = supplier()
        if result is not None:
            redis_client.setex(cache_key, expire_time, json.dumps(result))
        return result
