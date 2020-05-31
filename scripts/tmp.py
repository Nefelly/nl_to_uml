from litatom.model import UserSetting, UserRecord
from litatom.service import ForbidRecordService


def get_device_forbidden_num_by_uid(uuid):
    uids = UserSetting.get_uids_by_uuid(uuid)

    def add(x, y):
        return x + y

    return reduce(add, map(UserRecord.get_forbidden_num_by_uid, uids))


num = 0
res = 0
x = list()
for user in UserSetting.objects():
    uuid = user.uuid
    if not uuid or uuid in x:
        continue
    x.append(uuid)
    num += 1
    if get_device_forbidden_num_by_uid(uuid) >= 3:
        res += 1

print(num, res)
