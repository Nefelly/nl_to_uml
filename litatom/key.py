# coding: utf-8
# Redis.
REDIS_KEY_SMS_CODE = 'sms_code:{phone}'
TOKEN_BUCKET_KEY = 'token_bucket:{key}'
REDIS_KEY_SMS_LIMIT = 'sms_limit:{phone}'
REDIS_KEY_SESSION_USER = 'session_userid:{session}'
REDIS_KEY_USER_HUANXIN = 'user_huanxin:{user_id}'
REDIS_KEY_USER_AGE = 'user_age:{user_id}'
REDIS_ADMIN_USER = 'admin_username:{session}'
REDIS_ONLINE_GENDER = 'online:{gender}'
REDIS_ONLINE = 'online'
REDIS_USER_LAST_ACT = 'uid_act:{user_id}'   # 用户最后一次动作时间
REDIS_UID_GENDER = 'uid_gender:{user_id}'
REDIS_AGE_UID = 'age_uid:{age}'  # set
REDIS_USER_SEC_ACT = 'user_sec_act:{user_id}'
REDIS_USER_INFO_FINISHED = 'user_info_finished:{user_id}'  # 用户是否完成

REDIS_FAKE_START = 'fake_start:{fake_id}'   # 开始进入匹配
REDIS_USER_MATCH_LEFT = 'user_match_left:{user_date}'   # 过期时间一天
REDIS_FAKE_ID_UID = 'fakeid_uid:{fake_id}'
REDIS_UID_FAKE_ID = 'uid_fakeid:{user_id}'
REDIS_ANOY_GENDER_ONLINE = 'anoy_online:{gender}'   # sorted set
REDIS_ANOY_CHECK_POOL = 'anoy_check_pool'   # sorted set
REDIS_FAKE_ID_GENDER = 'fakeid_gender:{fake_id}'
REDIS_FAKE_ID_AGE = 'fakeid_age:{fake_id}'
REDIS_FAKE_LIKE = 'fake_like:{fake_id}'  # value fake_id
REDIS_MATCH_PAIR = 'match_start:{low_high_fakeid}'
REDIS_MATCHED = 'matched:{fake_id}'   # 双方匹配上, 匹配动作 需要同时填写 两个键值对
REDIS_GENDER_FEED_LIST = 'feeds_list:{gender}'   # sorted set
REDIS_USER_MESSAGES = 'user_messages:{user_id}'   #sortedset
REDIS_JUDGE_LOCK = 'judge_lock:{fake_id}'   # 评价对方的接口, 用于防范被刷评价

REDIS_HUANXIN_ACCESS_TOKEN = 'huanxin_access_token'
REDIS_HUANXIN_ACCESS_TOKEN_EXPIRE = 'huanxin_access_token_expire'
REDIS_LOCK = 'redis_lock:{key}'

# feed service
REDIS_FEED_SQUARE = 'feed_square'
REDIS_FEED_HQ = 'feed_hq'

