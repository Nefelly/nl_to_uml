import os
from litatom.service import AliOssService
from litatom.model import (
    Wording,
    Avatar
)
from litatom.const import (
    GENDERS
)

def up_wording():
    Wording.create('wait 3 mins to match', 'match_info')


def up_avatar():
    dirName = '/data/datas/Avatar'
    Avatar.objects().delete()
    for g in GENDERS:
        tmp = os.path.join(dirName, g)
        for f in os.listdir(tmp):
            fileName = os.path.join(tmp, f)
            fileid = AliOssService.upload_from_binary(open(fileName).read())
            Avatar.create(fileid, g)

if __name__ == "__main__":
    up_wording()
    up_avatar()
