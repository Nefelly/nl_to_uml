# coding: utf-8
import json
import time
import traceback
from ..model import (
    Tag,
    UserTag
)
from ..service import (
    GlobalizationService
)
import logging
from ..redis import RedisClient

logger = logging.getLogger(__name__)

redis_client = RedisClient()['lit']


class UserTagService(object):
    '''
    '''

    @classmethod
    def get_cached_tag(cls, name):
        return 'user_tag' + '_' + name.replace(' ', '_')

    @classmethod
    def get_tags(cls):
        raw_tags = Tag.get_tags()
        for i in range(len(raw_tags)):
            tag = cls.get_cached_tag(raw_tags[i]['name'])
            raw_tags[i]['name'] = GlobalizationService.get_cached_region_word(tag)
        return raw_tags, True

    @classmethod
    def add_tags(cls, user_id, tag_ids):
        for tag_id in tag_ids:
            UserTag.create(user_id, tag_id)
        return None, True

    @classmethod
    def ensure_tags(cls, user_id, tag_ids):
        UserTag.get_by_user_id(user_id).delete()
        for tag_id in tag_ids:
            obj = UserTag(user_id=user_id, tag_id=tag_id)
            obj.save()
        return True

    @classmethod
    def get_tag_id_tagnames_m(cls):
        res = {}
        tags, status = cls.get_tags()
        for el in tags:
            res[el['id']] = el['name']
        return res

    @classmethod
    def user_tags(cls, user_id):
        objs = UserTag.get_by_user_id(user_id)
        tag_names = cls.get_tag_id_tagnames_m()
        res = []
        for obj in objs:
            tmp = {
                'tag_id': obj.tag_id,
                'tag_name': tag_names.get(obj.tag_id)
            }
            res.append(tmp)
        return {'tags': res}, True
