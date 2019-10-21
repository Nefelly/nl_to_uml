# flake8: noqa
from .block import (
    Blocked
)
from .feed import (
    Feed,
    FeedLike,
    FeedComment,
    FollowingFeed
)
from .follow import (
    Follow
)
from .material import (
    Avatar,
    YoutubeVideo,
    Wording
)
from .report import (
    Report
)
from .feedback import (
    Feedback
)
from .user import (
    User,
    UserSetting,
    UserAction,
    HuanxinAccount,
    SocialAccountInfo,
    UserRecord,
    OnlineLimit,
    UserAddressList
)
from .user_message import (
    UserMessage
)
from .firebase import (
    FirebaseInfo
)
from .palm import (
    PalmResult
)
from .message import (
    HuanxinMessage
)
from .redis_lock import (
    RedisLock
)
from .track import TrackChat
from .admin import AdminUser
from .fbbackup import FaceBookBackup
from .globalization import RegionWord
from .referral_code import ReferralCode
from .user_model import LoginRecord
from ..db import DBManager


dbm = DBManager()
dbm.initall()