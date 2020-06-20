import os
from litatom.service import AliOssService
from litatom.model import (
    Wording,
    Avatar,
    Gift
)
from litatom.const import (
    GENDERS
)

def up_wording():
    pass
    Wording.create('wait 3 mins to match', 'match_info')


def up_avatar():
    dirName = '/data/datas/Avatar'
    # Avatar.objects().delete()
    for g in GENDERS:
        tmp = os.path.join(dirName, g)
        for f in os.listdir(tmp):
            fileName = os.path.join(tmp, f)
            fileid = AliOssService.upload_from_binary(open(fileName).read())
            Avatar.create(fileid, g)

def up_paied_avatar():
    dirName = '/data/tmp/2222'
    for g in GENDERS:
        tmp = os.path.join(dirName, g)
        for f in os.listdir(tmp):
            fileName = os.path.join(tmp, f)
            if '.png' not in fileName:
                print 'skip', fileName
                continue
            fileid = AliOssService.upload_from_binary(open(fileName).read())
            Avatar.create(fileid, g, True, 5)


def up_gift():
    Gift.objects().delete()
    dir_name = '/data/tmp/gifts'
    for f in os.listdir(dir_name):
        if '.zip' not in f:
            continue
        # zipid = AliOssService.upload_from_binary(f)
        thumbnail_add = f.replace(u'', '').replace('', '').replace('.zip', '.png')
        print thumbnail_add
        os.path.lexists(thumbnail_add)

if __name__ == "__main__":
    # up_wording()
    # up_avatar()
    # up_paied_avatar()
    up_gift()
