from litatom.const import BLOCK_PIC
from litatom.model import TrackSpamRecord
from litatom.service import ForbidCheckService


def run():
    for obj in TrackSpamRecord.objects(dealed=False):
        print(obj.id)
        if obj.word:
            print(obj.word)
            obj.forbid_weight = 2
            print(obj.forbid_weight)
        if obj.pic:
            reason,advice = ForbidCheckService.check_unknown_source_pics(obj.pic)
            if not reason:
                obj.forbid_weight = 0
            if advice == BLOCK_PIC:
                obj.forbid_weight = 4
            else:
                obj.forbid_weight = 0


if __name__ == '__main__':
    run()
