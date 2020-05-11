# coding: utf-8

WHOSYOURDADDY = 'IAMYOURDADDY'

ADMINISTRATORS = {
    '5e357b07f142533fff0049c2',         # 绿杨
    '5e651b6dad85ef6fb4664815',         # Norman,ID
    '5da849e33fff225cb55d1e73',         # 王贤思,VN
    '5e1d822b3fff223633a2ba2d',         # 乐乐,VN
    '5cebd0763fff225dc7f2bba5',         # Alice 麦明芳,ID
    '5e70414578e8443ea1ac48d2',         # 54, TH
}

SYS_FORBID = 'sysForbid'
MANUAL_FORBID = 'manualForbid'

REVIEW_PIC = 'R'
BLOCK_PIC = 'B'

LOGGING_PRDLINE = 'sns'
LOGGING_APP_NAME = 'sns-litatom'

REMOVE_EXCHANGE = 'remove_feed'
ADD_EXCHANGE = 'add_feed'

USER_ACTION_EXCHANGE = 'user_action_exchange'
COMMANDS_EXCHANGE = 'commands_exchange'
USER_MODEL_EXCHANGE = 'user_model_exchange'
ALI_LOG_EXCHANGE = 'ali_log_exchange'
#
# PIC_UPLOAD_EXCHANGE = 'feed_check'

# cookie 中的存 session 的 key
SESSION_SESSION_ID_KEY = 'sessionid.'
PLATFORM_IOS = 'ios'
PLATFORM_ANDROID = 'android'
DEFAULT_QUERY_LIMIT = 100
BOY = 'boy'
GIRL = 'girl'
GENDERS = [BOY, GIRL]
UNKNOWN_GENDER = 'unknown'
INT_BOY = 1
INT_GIRL = 0
TYPE_VOICE_AGORA = 'agora'
TYPE_VOICE_TENCENT = 'tencent'
CODE_PRIOR_VOICE = TYPE_VOICE_AGORA

BACKUP_HOST = 'http://www.litmatchapp.com'
BACKUP_DNS = 'litmatchapp'

ALL_FILTER = True

# 后端action
ACTION_ACCOST_OVER = 'accost_over'
ACTION_ACCOST_STOP = 'accost_stop'
ACTION_ACCOST_NEED_VIDEO = 'need_video'


# 提示消息
OPERATE_TOO_OFTEN = u'you have operate too quick, please try later~'
USER_NOT_EXISTS = u'user not exist, please register.'
PROFILE_NOT_COMPLETE = u'you must complete your profile first.'
CREATE_HUANXIN_ERROR = u'create huanxin failed.'
BLOCKED_MSG = u'you have been blocked'
BLOCK_OTHER_MSG = u'you have block the user'
NOT_IN_MATCH = u'you are not in a match.'
NOT_AUTHORIZED = u'you are not authorized to this action'
FORBID_INFO = u'Our system has noticed inappropriate behavior on your account. ' \
              u'You’ve been restricted until {unforbid_time}. In the future ' \
              u'please keep your chats positive. If you believe you’ve been ' \
              u'incorrectly flagged, you can contact our customer service team. '

NO_SET = 'noset'
ONE_MIN = 60
FIVE_MINS = 60 * 5
TEN_MINS = 60 * 10
HALF_HOUR = 60 * 30
ONE_HOUR = 60 * 60 * 1
TWO_HOURS = 60 * 60 * 2
SIX_HOURS = 60 * 60 * 6
ONE_DAY = 60 * 60 * 24
ONE_WEEK = 60 * 60 * 24 * 7
TWO_WEEKS = 60 * 60 * 24 * 14
ONE_MONTH = 60 * 60 * 24 * 30
FOREVER = 1200 * ONE_MONTH
FOREVER_FORBID_TS = 4102416000

MAX_DIAMONDS = 99999999

# redis中空集的占位符
NAN = 'NAN'

APP_PATH = '/data/apps/'
MAX_TIME = 2 * (10 ** 9)
ONLINE_LIVE = TWO_WEEKS
USER_ACTIVE = 2 * TEN_MINS
REAL_ACTIVE = 3 * ONE_MIN

CAN_MATCH_ONLINE = False
# USER_ACTIVE = 3 * ONE_MIN

#diamonds
