import os
import time
from litatom.redis import RedisClient
from litatom.service import GlobalizationService
from litatom.key import (
    REDIS_FEED_SQUARE,
    REDIS_FEED_SQUARE_REGION,
    REDIS_FEED_HQ,
    REDIS_FEED_HQ_REGION,
    REDIS_ONLINE_GENDER,
    REDIS_ONLINE_GENDER_REGION,
    REDIS_ONLINE,
    REDIS_ONLINE_REGION,
    REDIS_ANOY_GENDER_ONLINE,
    REDIS_ANOY_GENDER_ONLINE_REGION
)
from litatom.const import (
    GIRL,
    BOY
)

redis_client = RedisClient()['lit']

def copy(src, dst):
    for k, score in redis_client.zscan_iter(src):
        redis_client.zadd(dst, {k: score})


def rem():
    if os.getcwd().split('/')[-1] != 'devlitatom':
        print 'not right path'
        assert False
        exit()
    region = 'th'
    pairs = [
        [REDIS_FEED_SQUARE, REDIS_FEED_SQUARE_REGION.format(region=region)],
        [REDIS_FEED_HQ, REDIS_FEED_HQ_REGION.format(region=region)],
        [REDIS_ONLINE, REDIS_ONLINE_REGION.format(region=region)],
        [REDIS_ONLINE_GENDER.format(gender=GIRL), REDIS_ONLINE_GENDER_REGION.format(region=region, gender=GIRL)],
        [REDIS_ONLINE_GENDER.format(gender=BOY), REDIS_ONLINE_GENDER_REGION.format(region=region, gender=BOY)],
        [REDIS_ANOY_GENDER_ONLINE.format(gender=GIRL), REDIS_ANOY_GENDER_ONLINE_REGION.format(region=region, gender=GIRL)],
        [REDIS_ANOY_GENDER_ONLINE.format(gender=BOY), REDIS_ANOY_GENDER_ONLINE_REGION.format(region=region, gender=BOY)]

    ]
    for src, dst in pairs:
        redis_client.delete(src)

def all_copy():
    region = 'th'
    pairs = [
        [REDIS_FEED_SQUARE, REDIS_FEED_SQUARE_REGION.format(region=region)],
        [REDIS_FEED_HQ, REDIS_FEED_HQ_REGION.format(region=region)],
        [REDIS_ONLINE, REDIS_ONLINE_REGION.format(region=region)],
        [REDIS_ONLINE_GENDER.format(gender=GIRL), REDIS_ONLINE_GENDER_REGION.format(region=region, gender=GIRL)],
        [REDIS_ONLINE_GENDER.format(gender=BOY), REDIS_ONLINE_GENDER_REGION.format(region=region, gender=BOY)],
        [REDIS_ANOY_GENDER_ONLINE.format(gender=GIRL), REDIS_ANOY_GENDER_ONLINE_REGION.format(region=region, gender=GIRL)],
        [REDIS_ANOY_GENDER_ONLINE.format(gender=BOY), REDIS_ANOY_GENDER_ONLINE_REGION.format(region=region, gender=BOY)]

    ]
    for src, dst in pairs:
        print 'start to copy: %s to %s' % (src, dst)
        copy(src, dst)
    print 'success'


if __name__ == "__main__":
    all_copy()
    #rem()
