import os
import time
from litatom.service import FollowingFeedService
from litatom.model import (
    Follow,
    User
)

def deal_followings():
    for follow in Follow.objects():
        user_id = follow.uid
        followed_user_id = follow.followed
        print 'deal: user_id:%s, followed_user_id:%s' % (user_id, followed_user_id)
        FollowingFeedService.add_following(user_id, followed_user_id)
    for user in User.objects():
        user_id = str(user.id)
        FollowingFeedService.add_following(user_id, user_id)

if __name__ == "__main__":
    deal_followings()
