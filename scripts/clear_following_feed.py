import os
import time
from litatom.service import (
    MaintainService
)


if __name__ == "__main__":
    print "started at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
    MaintainService.clear_following_feed()
    MaintainService.clear_UserMessages()
    MaintainService.clear_user_conversations()
    print "ended at", time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
