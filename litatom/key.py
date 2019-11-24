# coding: utf-8
# Redis.
REDIS_KEY_SMS_CODE = 'sms_code:{phone}'
TOKEN_BUCKET_KEY = 'token_bucket:{key}'
REDIS_KEY_SMS_LIMIT = 'sms_limit:{phone}'
REDIS_KEY_SESSION_USER = 'session_userid:{session}'
REDIS_KEY_USER_HUANXIN = 'user_huanxin:{user_id}'
REDIS_KEY_USER_AGE = 'user_age:{user_id}'
REDIS_ADMIN_USER = 'admin_username:{session}'
REDIS_REGION_TAG_WORD = 'region_tag:{region_tag}'
REDIS_USER_LOC = 'user_loc:{user_id}'
REDIS_USER_REGION = 'user_region:{user_id}'
REDIS_HUANXIN_USER = 'huanxin_user:{huanxin_id}'
REDIS_FEED_ID_AGE = 'feed_id_age:{feed_id}'
REDIS_AD_TIMES_LEFT = 'ad_times_left:{user_date}'
REDIS_REGION_FEED_TOP = 'region_feed_top:{region}'

# cache
REDIS_USER_CACHE = 'user_cache:{user_id}'
REDIS_USER_ACCOUNT_CACHE = 'user_account_cache:{user_id}'
REDIS_USER_SETTING_CACHE = 'user_setting_cache:{user_id}'
REDIS_USER_MODEL_CACHE = 'user_model_cache:{user_id}'
REDIS_FEED_CACHE = 'feed_cache:{feed_id}'
REDIS_AVATAR_CACHE = 'avatar_cache'
REDIS_YOUTUBE_VIDEO_CACHE = 'youtube_video_cache:{region}'
REDIS_FEED_LIKE_CACHE = 'feed_like_cache:{feed_id}'
REDIS_USER_NOT_MESSAGE_CACHE = 'user_nomsg_cache:{user_id}'
REDIS_ACCELERATE_CACHE = 'acclerate_cache:{user_id}'
REDIS_ONLINE_CNT_CACHE = 'online_cnt_cache:{region}:{gender}'

REDIS_HUANXIN_ONLINE = 'huanxin_online'
REDIS_ONLINE_GENDER_REGION = 'online:{gender}:{region}'
REDIS_ONLINE_REGION = 'online:{region}'   # !!!

REDIS_USER_LAST_ACT = 'uid_act:{user_id}'   # 用户最后一次动作时间
REDIS_UID_GENDER = 'uid_gender:{user_id}'
REDIS_AGE_UID = 'age_uid:{age}'  # set
REDIS_USER_SEC_ACT = 'user_sec_act:{user_id}'
REDIS_USER_INFO_FINISHED = 'user_info_finished:{user_id}'  # 用户是否完成

REDIS_FAKE_START = 'fake_start:{fake_id}'   # 开始进入匹配
REDIS_USER_MATCH_LEFT = 'user_match_left:{user_date}'   # 过期时间一天
REDIS_FAKE_ID_UID = 'fakeid_uid:{fake_id}'
REDIS_UID_FAKE_ID = 'uid_fakeid:{user_id}'

REDIS_ANOY_GENDER_ONLINE_REGION = 'anoy_online:{gender}:{region}'   # sorted set   # !!!

REDIS_ACCELERATE_REGION_TYPE_GENDER = 'accelerate_online:{match_type}:{region}:{gender}'

REDIS_ANOY_CHECK_POOL = 'anoy_check_pool'   # sorted set
REDIS_FAKE_ID_GENDER = 'fakeid_gender:{fake_id}'
REDIS_FAKE_ID_AGE = 'fakeid_age:{fake_id}'
REDIS_FAKE_LIKE = 'fake_like:{fake_id}'  # value fake_id
REDIS_MATCH_PAIR = 'match_start:{low_high_fakeid}'
REDIS_MATCH_BEFORE = 'match_before:{low_high_fakeid}'
REDIS_MATCH_BEFORE_PREFIX = 'match_before:'
REDIS_MATCHED = 'matched:{fake_id}'   # 双方匹配上, 匹配动作 需要同时填写 两个键值对
REDIS_JUDGE_LOCK = 'judge_lock:{fake_id}'   # 评价对方的接口, 用于防范被刷评价

REDIS_USER_MESSAGES = 'user_messages:{user_id}'   #sortedset
REDIS_HUANXIN_ACCESS_TOKEN = 'huanxin_access_token'
REDIS_HUANXIN_ACCESS_TOKEN_EXPIRE = 'huanxin_access_token_expire'
REDIS_LOCK = 'redis_lock:{key}'

# feed service
REDIS_FEED_SQUARE_REGION = 'feed_square:{region}'   # !!!
REDIS_FEED_HQ_REGION = 'feed_hq:{region}'   # !!!

# voice match
REDIS_USER_VOICE_MATCH_LEFT = 'voice_user_match_left:{user_date}'   # 过期时间一天
REDIS_VOICE_FAKE_ID_UID = 'voice_fakeid_uid:{fake_id}'
REDIS_VOICE_UID_FAKE_ID = 'voice_uid_fakeid:{user_id}'
REDIS_VOICE_FAKE_START = 'voice_fake_start:{fake_id}'   # 开始进入匹配
REDIS_VOICE_ANOY_CHECK_POOL = 'voice_anoy_check_pool'   # sorted set
REDIS_VOICE_MATCH_PAIR = 'voice_match_start:{low_high_fakeid}'
REDIS_VOICE_MATCHED_BEFORE = 'voice_match_before:{low_high_fakeid}'
REDIS_VOICE_MATCHED = 'voice_matched:{fake_id}'   # 双方匹配上, 匹配动作 需要同时填写 两个键值对
REDIS_VOICE_FAKE_LIKE = 'voice_fake_like:{fake_id}'  # value fake_id
REDIS_VOICE_JUDGE_LOCK = 'voice_judge_lock:{fake_id}'   # 评价对方的接口, 用于防范被刷评价
REDIS_VOICE_GENDER_ONLINE_REGION = 'voice_online:{gender}:{region}'
REDIS_VOICE_SDK_TYPE = 'voice_sdk_type:{user_id}'

#voice chat
REDIS_VOICE_CHAT_WAIT = 'voice_chat_wait:{user_id}'
REDIS_VOICE_CHAT_CALLED = 'voice_chat_called:{user_id}'
REDIS_VOICE_CHAT_IN_CHAT = 'voice_chat_in_chat:{user_id}'


# video match
REDIS_USER_VIDEO_MATCH_LEFT = 'video_user_match_left:{user_date}'   # 过期时间一天
REDIS_VIDEO_FAKE_ID_UID = 'video_fakeid_uid:{fake_id}'
REDIS_VIDEO_UID_FAKE_ID = 'video_uid_fakeid:{user_id}'
REDIS_VIDEO_FAKE_START = 'video_fake_start:{fake_id}'   # 开始进入匹配
REDIS_VIDEO_ANOY_CHECK_POOL = 'video_anoy_check_pool'   # sorted set
REDIS_VIDEO_MATCH_PAIR = 'video_match_start:{low_high_fakeid}'
REDIS_VIDEO_MATCHED_BEFORE = 'video_match_before:{low_high_fakeid}'
REDIS_VIDEO_VID = 'video_match_vid:{low_high_fakeid}'
REDIS_VIDEO_MATCHED = 'video_matched:{fake_id}'   # 双方匹配上, 匹配动作 需要同时填写 两个键值对
REDIS_VIDEO_FAKE_LIKE = 'video_fake_like:{fake_id}'  # value fake_id
REDIS_VIDEO_JUDGE_LOCK = 'video_judge_lock:{fake_id}'   # 评价对方的接口, 用于防范被刷评价
REDIS_VIDEO_GENDER_ONLINE_REGION = 'video_online:{gender}:{region}'

#video chat
REDIS_VIDEO_CHAT_WAIT = 'video_chat_wait:{user_id}'
REDIS_VIDEO_CHAT_CALLED = 'video_chat_called:{user_id}'
REDIS_VIDEO_CHAT_IN_CHAT = 'video_chat_in_chat:{user_id}'

# dev owned
REDIS_SETTINGS_KEYS = 'dev_settings'
