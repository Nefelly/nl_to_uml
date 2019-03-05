# flake8: noqa
from .block import (
    Blocked
)
from .feed import (
    Feed,
    FeedLike,
    FeedComment
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
from .user import (
    User,
    UserSetting,
    UserAction
)
from .user_message import (
    UserMessage
)
from .redis_lock import (
    RedisLock
)

from ..db import DBManager

dbm = DBManager()
dbm.initall()