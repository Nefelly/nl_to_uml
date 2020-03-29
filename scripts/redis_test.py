from litatom.redis import RedisClient

redis_client = RedisClient()['lit']


def run():
    res1 = redis_client.sadd('test_ret', 1)
    if res1:
        print('res1:', res1)
    res2 = redis_client.sadd('test_ret', 2)
    if res2:
        print('res2:', res2)
    res3 = redis_client.sadd('test_ret', 1)
    if res3:
        print('res3', res3)


if __name__ == '__main__':
    run()
