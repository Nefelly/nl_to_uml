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
    OnlineLimit
)
from .user_message import (
    UserMessage
)
from .firebase import (
    FirebaseInfo
)
from .redis_lock import (
    RedisLock
)
from .track import TrackChat
from .admin import AdminUser
from .fbbackup import FaceBookBackup
from .globalization import RegionWord
from ..db import DBManager


dbm = DBManager()
dbm.initall()