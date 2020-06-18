# flake8: noqa
from .block import (
    Blocked
)
from .feed import (
    Feed,
    FeedLike,
    FeedDislike,
    FeedComment,
    FollowingFeed
)
from .acted_record import (
    ActedRecord
)
from .follow import (
    Follow
)
from .material import (
    Avatar,
    YoutubeVideo,
    Wording,
    SpamWord,
    FakeSpamWord,
    HitTagWord
)
from .gift import (
    Gift,
    ReceivedGift
)
from . visit_record import (
    VisitRecord,
    NewVisit
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
    UserAddressList,
    BlockedDevices
)
from .user_message import (
    UserMessage,
    UserConversation
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
from .journal import StatItems
from .track import (
    TrackChat,
    TrackSpamRecord
)
from .experiment import (
    ExpBucket
)
from .user_account import (
    UserAccount,
    AccountFlowRecord,
    UserAsset
)
from .admin import (
    AdminUser,
    AppAdmin
)
from .debug_models import (
    UserLogs
)
from .fbbackup import FaceBookBackup
from .globalization import RegionWord
from .referral_code import ReferralCode
from .user_model import (
    UserModel,
    Uuids
)
from .match_record import (
    MatchRecord,
    MatchHistory,
    VoiceMatchRecord
)
from .tag import (
    Tag,
    UserTag
)
from .experiment_result import ExperimentResult
from .operate_record import OperateRecord
from .anoy_online import AnoyOnline
from ..db import DBManager


dbm = DBManager()
dbm.initall()