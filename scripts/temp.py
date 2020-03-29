from litatom.redis import RedisClient
from litatom.service import ShareStatService

redis_client=RedisClient()['lit']


def run():
    key=ShareStatService.get_clicker_key('101.94.131.160')
    redis_client.set(key,1)


if __name__ == '__main__':
    run()
