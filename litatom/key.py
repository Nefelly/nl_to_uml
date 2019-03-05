# coding: utf-8
# Redis.
REDIS_KEY_SMS_CODE = 'sms_code:{phone}'
REDIS_KEY_SESSION_USER = 'session_userid:{session}'
REDIS_ONLINE_GENDER = 'online:{gender}'
REDIS_USER_LAST_ACT = 'uid_act:{user_id}'   # 用户最后一次动作时间
REDIS_UID_GENDER = 'uid_gender:{user_id}'
REDIS_AGE_UID = 'age_uid:{age}'  # set
REDIS_USER_SEC_ACT = 'user_sec_act:{user_id}'
REDIS_USER_MATCH_LEFT = 'user_match_left:{user_date}'   # 过期时间一天

REDIS_FAKE_START = 'fake_start:{fake_id}'
REDIS_FAKE_ID_UID = 'fakeid_uid:{fake_id}'
REDIS_FAKE_ID_GENDER = 'fakeid_gender:{fake_id}'
REDIS_FAKE_ID_AGE = 'fakeid_age:{fake_id}'
REDIS_FAKE_LIKE = 'fake_like:{fake_id}'  # value fake_id
REDIS_MATCH_START = 'match_start:{low_high_fakeid}'
REDIS_MATCHED = 'matched:{fake_id}'   # 双方匹配上, 匹配动作 需要同时填写 两个键值对
REDIS_GENDER_FEED_LIST = 'feeds_list:{gender}'   # sorted set
REDIS_USER_MESSAGES = 'user_messages:{user_id}'   #sortedset

REDIS_HUANXIN_ACCESS_TOKEN = 'huanxin_access_token'

