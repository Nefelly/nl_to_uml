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
    dir_name = '/data/tmp/gifts/'
    from xpinyin import Pinyin
    for f in os.listdir(dir_name):
        if '.zip' not in f:
            continue
        zip_add = dir_name + f
        thumbnail_add = f.replace('-动画文件', '').replace('动画文件', '').replace('.zip', '.png')
        thumbnail_add = dir_name + thumbnail_add
        if not os.path.exists(zip_add) or not os.path.exists(thumbnail_add):
            assert False, 'not file zip:%s thumb:%s' % (zip_add, thumbnail_add)
        print thumbnail_add
        zipid = AliOssService.upload_from_binary(open(zip_add).read())
        thumbnail_id = AliOssService.upload_from_binary(open(thumbnail_add).read())
        p = Pinyin()
        name = p.get_pinyin(thumbnail_add.split('/')[-1].replace('.png', '').decode('utf8'))
        print name, '!' * 10, thumbnail_id
        Gift.create(zipid, thumbnail_id, 5, name)

if __name__ == "__main__":
    # up_wording()
    # up_avatar()
    # up_paied_avatar()
    up_gift()
