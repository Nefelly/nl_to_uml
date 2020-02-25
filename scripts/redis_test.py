from litatom.redis import RedisClient
redis_client = RedisClient()['lit']

def run():
    redis_client.set('test',1)
    redis_client.expire('test',60)
    a= redis_client.get('test')
    print(a,type(a))

if __name__ == '__main__':
    run()