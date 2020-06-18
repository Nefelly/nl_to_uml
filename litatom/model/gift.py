# coding: utf-8
import datetime
import random
import cPickle
import bson
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)
from ..util import (
    date_to_int_time
)
from .. key import (
    REDIS_GIFT_CACHE,
    REDIS_GIFT_PRICE_CACHE
)
from ..const import (
    ONE_DAY
)
from ..redis import RedisClient

sys_rnd = random.SystemRandom()
redis_client = RedisClient()['lit']


class Gift(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    fileid = StringField(required=True)
    thumbnail = StringField()
    price = IntField(default=0)
    recycle_price = IntField(default=0)
    name = StringField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, fileid, thumbnail, price, name, recycle_price=0):
        obj = cls(fileid=fileid, thumbnail=thumbnail, price=price, name=name, recycle_price=recycle_price)
        obj.save()
        cls._disable_cache()

    @classmethod
    def _disable_cache(cls):
        redis_client.delete(REDIS_GIFT_CACHE)
        redis_client.delete(REDIS_GIFT_PRICE_CACHE)

    @classmethod
    def get_by_id(cls, gift_id):
        return cls.objects(id=gift_id).first()

    def save(self, *args, **kwargs):
        if getattr(self, 'id', ''):
            self._disable_cache()
        super(Gift, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if getattr(self, 'id', ''):
            self._disable_cache()
        super(Gift, self).delete(*args, **kwargs)

    @classmethod
    def get_gifts(cls):
        cache_obj = redis_client.get(REDIS_GIFT_CACHE)
        if cache_obj:
            return cPickle.loads(cache_obj)
        gifts = []
        for obj in cls.objects().order_by('price'):
            gifts.append(obj.to_json())
        redis_client.set(REDIS_GIFT_CACHE, cPickle.dumps(gifts))
        return gifts

    @classmethod
    def gift_price_m(cls):
        cache_obj = redis_client.get(REDIS_GIFT_PRICE_CACHE)
        if cache_obj:
            return cPickle.loads(cache_obj)
        gifts = {}
        for obj in cls.objects():
            gifts[str(obj.id)] = obj.price
        redis_client.set(REDIS_GIFT_PRICE_CACHE, cPickle.dumps(gifts))
        return gifts

    def to_json(self):
        return {
            'id': str(self.id),
            'price': self.price,
            'name': self.name,
            'fileid': self.fileid,
            'thumbnail': self.thumbnail,
            'create_time': self.create_time
        }


class ReceivedGift(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    sender = StringField(required=True)
    receiver = StringField(required=True)
    gift_id = StringField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_by_receiver_id(cls, receiver, page_num=0, num=20):
        start_num = page_num * num
        return cls.objects(receiver=receiver).order_by('-create_time').skip(start_num).limit(num)


    @classmethod
    def create(cls, sender, receiver, gift_id):
        obj = cls(sender=sender, receiver=receiver, gift_id=gift_id)
        obj.save()
        return True

    def to_json(self):
        result = {}
        for key in self._fields:
            attr = getattr(self, key)
            if key == 'id':
                attr = str(attr)
            elif key == 'create_time':
                attr = date_to_int_time(attr)
            result[key] = attr
        return result
