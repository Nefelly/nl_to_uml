# coding: utf-8
import datetime
import cPickle
import json
from mongoengine import (
    BooleanField,
    DateTimeField,
    Document,
    IntField,
    ListField,
    StringField,
)
from ..redis import RedisClient
from ..const import (
    GENDERS
)
from ..key import (
    REDIS_AVATAR_CACHE,
    REDIS_YOUTUBE_VIDEO_CACHE,
    REDIS_SPAM_WORD_CACHE,
    REDIS_FAKE_SPAM_WORD_CACHE,
    REDIS_FEED_TAG_WORD_CACHE
)
redis_client = RedisClient()['lit']

class Avatar(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    PAID_SUFFIX = '_paid'
    fileid = StringField(required=True)
    gender = StringField(required=False)
    paid = BooleanField(required=True, default=False)
    price = IntField(default=0)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, fileid, gender, paid=False, price=0):
        obj = cls(fileid=fileid, gender=gender, paid=paid, price=price)
        obj.save()
        cls._disable_cache()

    @classmethod
    def paid_keys(cls):
        return [g + cls.PAID_SUFFIX for g in GENDERS]

    @classmethod
    def _disable_cache(cls):
        redis_client.delete(REDIS_AVATAR_CACHE)

    def save(self, *args, **kwargs):
        super(Avatar, self).save(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache()

    def delete(self, *args, **kwargs):
        super(Avatar, self).delete(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache()

    @classmethod
    def get_avatars(cls):
        cache_obj = redis_client.get(REDIS_AVATAR_CACHE)
        if cache_obj:
            return cPickle.loads(cache_obj)

        avatars = {}
        # load not paid avatar
        for g in GENDERS:
            if not avatars.get(g):
                avatars[g] = []
            objs = cls.objects(gender=g, paid__ne=True)
            for obj in objs:
                fileid = obj.fileid
                avatars[g].append(fileid)
        # print avatars
        # laod paid avatar
        for g in GENDERS:
            paid_key = g + cls.PAID_SUFFIX
            avatars[paid_key] = {}
            for obj in cls.objects(gender=g, paid=True):
                avatars[paid_key][obj.fileid] = {'price': obj.price, 'owned': False}
        # print avatars
        redis_client.set(REDIS_AVATAR_CACHE, cPickle.dumps(avatars))
        return avatars

    @classmethod
    def get_paid_avatars(cls):
        avatars = cls.get_avatars()
        res = {}
        for g in GENDERS:
            paid_key = g + cls.PAID_SUFFIX
            res.update(avatars.get(paid_key, {}))
        return res

    @classmethod
    def valid_avatar(cls, fileid):
        avatars = cls.get_avatars()
        for paied in [False, True]:
            for gender in GENDERS:
                g = gender if not paied else gender + cls.PAID_SUFFIX
                if fileid in avatars.get(g, {}):
                    return True
        return False

# Avatar.test()


class YoutubeVideo(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    vid = StringField(required=True)
    region = StringField(required=True)
    info = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, vid, region, info):
        if not isinstance(info, dict):
            return False
        info = json.dumps(info)
        obj = cls.get_by_vid_region(vid, region)
        if obj:
            obj.info = info
            obj.save()
        else:
            obj = cls(vid=vid, region=region, info=info)
            obj.save()
        cls._disable_cache(region=region)
        return True

    @classmethod
    def info_by_vid(cls, vid):
        obj = cls.objects(vid=vid).first()
        if not obj:
            return {}
        return obj.get_info()

    @classmethod
    def get_by_vid_region(cls, vid, region):
        obj = cls.objects(vid=vid, region=region).first()
        return obj

    @classmethod
    def _disable_cache(cls, region):
        redis_client.delete(REDIS_YOUTUBE_VIDEO_CACHE.format(region=region))

    def save(self, *args, **kwargs):
        super(YoutubeVideo, self).save(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache(self.region)

    def delete(self, *args, **kwargs):
        super(YoutubeVideo, self).delete(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache(self.region)

    def get_info(self):
        info = json.loads(self.info)
        info.update({"video_id": self.vid})
        return info

    @classmethod
    def get_video_infos(cls, region):
        cache_key = REDIS_YOUTUBE_VIDEO_CACHE.format(region=region)
        cache_obj = redis_client.get(cache_key)
        if cache_obj:
            return cPickle.loads(cache_obj)
        videos = []
        objs = cls.objects(region=region)
        for obj in objs:
            videos.append(obj.get_info())
        redis_client.set(cache_key, cPickle.dumps(videos))
        return videos


class SpamWord(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    region = StringField(required=True)
    word = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, region, word):
        obj = cls.objects(region=region, word=word).first()
        if obj:
            return
        obj = cls(region=region, word=word)
        obj.save()

    @classmethod
    def get_by_region(cls, region):
        return cls.objects(region=region)

    @classmethod
    def _disable_cache(cls, region):
        redis_client.delete(REDIS_SPAM_WORD_CACHE.format(region=region))

    def save(self, *args, **kwargs):
        super(SpamWord, self).save(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache(self.region)

    def delete(self, *args, **kwargs):
        super(SpamWord, self).delete(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache(self.region)

    @classmethod
    def get_spam_words(cls, region):
        cache_key = REDIS_SPAM_WORD_CACHE.format(region=region)
        cache_obj = redis_client.get(cache_key)
        if cache_obj:
            return cPickle.loads(cache_obj)
        words = []
        objs = cls.objects(region=region)
        for obj in objs:
            words.append(obj.word)
        redis_client.set(cache_key, cPickle.dumps(words))
        return words
    

class FakeSpamWord(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    region = StringField(required=True)
    word = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, region, word):
        obj = cls.objects(region=region, word=word).first()
        if obj:
            return
        obj = cls(region=region, word=word)
        obj.save()

    @classmethod
    def get_by_region(cls, region):
        return cls.objects(region=region)

    @classmethod
    def _disable_cache(cls, region):
        redis_client.delete(REDIS_FAKE_SPAM_WORD_CACHE.format(region=region))

    def save(self, *args, **kwargs):
        super(FakeSpamWord, self).save(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache(self.region)

    def delete(self, *args, **kwargs):
        super(FakeSpamWord, self).delete(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache(self.region)

    @classmethod
    def get_spam_words(cls, region):
        cache_key = REDIS_FAKE_SPAM_WORD_CACHE.format(region=region)
        cache_obj = redis_client.get(cache_key)
        if cache_obj:
            return cPickle.loads(cache_obj)
        words = []
        objs = cls.objects(region=region)
        for obj in objs:
            words.append(obj.word)
        redis_client.set(cache_key, cPickle.dumps(words))
        return words


class HitTagWord(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }
    region = StringField(required=True)
    word = StringField(required=False)
    tag = StringField()
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def get_tags(cls):
        return cls.objects().distinct('tag')

    @classmethod
    def create(cls, tag, region, word):
        obj = cls.objects(tag=tag, region=region, word=word).first()
        if obj:
            return
        obj = cls(tag=tag, region=region, word=word)
        obj.save()

    @classmethod
    def get_by_region_tag(cls, region, tag):
        return cls.objects(region=region, tag=tag)

    @classmethod
    def _disable_cache(cls, region, tag):
        redis_client.delete(REDIS_FEED_TAG_WORD_CACHE.format(region=region, tag=tag))

    def save(self, *args, **kwargs):
        super(HitTagWord, self).save(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache(self.region, self.tag)

    def delete(self, *args, **kwargs):
        super(HitTagWord, self).delete(*args, **kwargs)
        if getattr(self, 'id', ''):
            self._disable_cache(self.region, self.tag)

    @classmethod
    def get_tag_words(cls, region, tag):
        cache_key = REDIS_FEED_TAG_WORD_CACHE.format(region=region, tag=tag)
        cache_obj = redis_client.get(cache_key)
        if cache_obj:
            return cPickle.loads(cache_obj)
        words = []
        objs = cls.objects(region=region)
        for obj in objs:
            words.append(obj.word)
        redis_client.set(cache_key, cPickle.dumps(words))
        return words


class Wording(Document):
    meta = {
        'strict': False,
        'alias': 'db_alias'
    }

    word_type = StringField(required=True)
    content = StringField(required=False)
    create_time = DateTimeField(required=True, default=datetime.datetime.now)

    @classmethod
    def create(cls, content, word_type):
        obj = cls.objects(word_type=word_type).first()
        if obj:
            return 
        obj = cls(content=content, word_type=word_type)
        obj.save()
    
    @classmethod
    def get_word_type(cls, word_type):
        if getattr(cls, 'word_types', None):
            return cls.word_types.get(word_type, '')
        cls.word_types = {}
        for obj in cls.objects():
            cls.word_types[obj.word_type] = obj.content
        return cls.word_types.get(word_type, '')