# coding: utf-8
import json
import time
import traceback
from ..model import (
    Tag,
    UserTag
)
from ..const import (
    ONE_DAY
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
        if not tag_ids:
            UserTag._disable_cache(user_id)
        for tag_id in tag_ids:
            obj = UserTag(user_id=user_id, tag_id=tag_id)
            obj.save()
        return None, True

    @classmethod
    def get_tag_id_tagnames_m(cls):
        res = {}
        tags, status = cls.get_tags()
        for el in tags:
            res[el['id']] = el['name']
        return res

    @classmethod
    def tags_str(cls, user_id):
        user_tag, status = cls.user_tags(user_id)
        if status and user_tag and user_tag.get('tags'):
            raw_tags = user_tag.get('tags')
            for el in raw_tags:
                if not el.get('tag_name'):
                    print el
            return ', '.join([el.get('tag_name') for el in raw_tags])
        return ''

    @classmethod
    def user_tags(cls, user_id):
        tag_key = UserTag.get_cached_key(user_id)
        cached_res = redis_client.get(tag_key)
        if cached_res:
            return json.loads(cached_res), True
        objs = UserTag.get_by_user_id(user_id)
        tag_names = cls.get_tag_id_tagnames_m()
        res = []
        for obj in objs:
            tag_name = tag_names.get(obj.tag_id)
            if not tag_name:
                obj.delete()
            tmp = {
                'tag_id': obj.tag_id,
                'tag_name': tag_name
            }
            res.append(tmp)
        ret = {'tags': res}
        cached_res = json.dumps(ret)
        redis_client.set(UserTag.get_cached_key(user_id), cached_res, ONE_DAY)
        return ret, True

    @classmethod
    def add_region_word(cls):
        from ..model import RegionWord
        for el in Tag.objects():
            tag = cls.get_cached_tag(el.name)
            RegionWord.add_or_mod(RegionWord.REGION_BENCHMARK, tag, el.name)

    @classmethod
    def test_data_set(cls):
        names = ["Free Fire", "Mobile Legends", "Pubg",
                 "Garena RoV", "KartRider Rush+", "Lainnya",
                 "Voice match", "Night owl",
                 "Movie lover", "Cat person", "Dog addict",
                 "Music", "Dancer", "Lonely", "want chatting",
                 "Lovely", "Reading"]
        # Tag.objects().delete()
        for name in names:
            Tag.create(name)
            cls.add_region_word()
        # from ..model import User
        # user_id = str(User.get_by_phone('8618938951380').id)
        # for el in Tag.objects():
        #     cls.add