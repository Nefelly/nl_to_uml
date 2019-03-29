import os
import time
from litatom.service import AnoyMatchService
from litatom.model import *

def clear_objs():
    for cls in [Blocked, Feed, FeedLike, FeedComment, Follow, Report, Feedback,
                UserAction, UserRecord, UserMessage]:
        cls.objects().delete()

if __name__ == "__main__":
    print "started at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    AnoyMatchService.clean_pools()
    print "ended at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    clear_objs()