from litatom.const import BLOCK_PIC
from litatom.model import TrackSpamRecord
from litatom.service import ForbidCheckService


def run():
    for obj in TrackSpamRecord.objects(dealed=False):
        if obj.word:
            obj.forbid_weight = 2
        if obj.pic:
            pic_res = ForbidCheckService.check_unknown_source_pics(obj.pic)
            if not pic_res:
                obj.forbid_weight = 0
            if pic_res[0][1] == BLOCK_PIC:
                obj.forbid_weight = 4
            else:
                obj.forbid_weight = 0


if __name__ == '__main__':
    run()
