from litatom.model import UserSetting, UserRecord
from litatom.service import MongoSyncService


def get_device_forbidden_num_by_uid(uuid):
    uids = UserSetting.get_uids_by_uuid(uuid)

    def add(x, y):
        return x + y

    return reduce(add, map(UserRecord.get_forbidden_num_by_uid, uids))


num = 0
res = 0
x = list()
table = MongoSyncService.load_table_map(UserSetting, 'user_id', 'uuid')
for user in table:
    uuid = table[user]
    if not uuid or uuid in x:
        continue
    x.append(uuid)
    num += 1
    if get_device_forbidden_num_by_uid(uuid) >= 3:
        res += 1
        if res % 10000 == 0:
            print(num, res)

print(num, res)
