# encoding:utf-8
from litatom.service import AliLogService
from litatom.model import User
from litatom.util import *


def run():
    to_time = get_zero_today()
    from_time = next_date(get_zero_today(),-1)
    print(from_time,to_time)
    users = User.get_by_create_time(from_time,to_time)
    print(users)
    for user in users:
        print(str(user.id))

if __name__ == '__main__':
    run()
