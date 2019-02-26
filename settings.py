# coding: utf-8
from hendrix.const import ENV_PROD, INTEGRATION_MODE_COMPONENT
from hendrix.util import EnvvarReader

_envvars = [
    'HENDRIX_ENV',
    'ASURA_CHECK_SIGN',

    # Docker,
    'IN_CONTAINER',

    # Sentry
    'SENTRY_ENABLED',
    'SENTRY_DSN',

    # database
    'DB_PROD',
    'DB_ATHENA',
    'DB_PROD_6001',
    'DB_PROD_6003',
    'DB_PROD_30006',
    'DB_SNS_MESSAGE',
    'DB_SNS_MESSAGE_NEW',
    'DB_SNS_NOTE',
    'DB_SNS_NOTE_NEW',
    'DB_SNS_NOTE_6003',
    'DB_PAGE',
    'DB_SNS_USER_RELATIONSHIP',
    'DB_SNS_USER_RELATIONSHIP_6002',
    'DB_SNS_1',
    'DB_SNS_1_NEW',
    'DB_SNS_1_SPVNOTE',
    'DB_POI',
    'DB_POI_NEW',
    'DB_BOARD',
    'DB_BOARD_NEW',
    'DB_ACTIVITY',
    'DB_ACTIVITY_6003',
    'DB_ACTIVITY_6004',
    'DB_USER',
    'DB_USER_NEW',
    'DB_IDOL_PRODUCER',
    'DB_ADS',
    'DB_SQUAD_PAGE',
    'DB_NEW_USER_FEED',
    'DB_DATA_SEM',
    'DB_SNS_WXMP_ACTIVITY',

    # redis
    'REDIS_SNS_TAG_LIKE',
    'REDIS_SNS_TAG_LIKE_CORVUS',
    'REDIS_NOTE_LIKE_CORVUS',
    'REDIS_NOTE_VIEW_CORVUS',
    'REDIS_NOTE_RELATED_GOODS',
    'REDIS_USER_MSG',
    'REDIS_USER_FOLLOW',
    'REDIS_USER_FOLLOW_CORVUS',
    'REDIS_BLOCKED_USER_CORVUS',
    'REDIS_USER_FANS_CORVUS',
    'REDIS_INTER_USER',
    'REDIS_USER_INFO_CORVUS',
    'REDIS_USER_SESSION_CORVUS',
    'REDIS_USER_CACHE_CORVUS',
    'REDIS_FEATURED_PAGE_INFO',
    'REDIS_NOTE_VIEW',
    'REDIS_THRONE',
    'REDIS_USER_RECOMMEND',
    'REDIS_NOTE_RED_PACKET',
    'REDIS_PEAK_NOTE',
    'REDIS_MESSAGE_AGGREGATION',
    'REDIS_COMMENT_CORVUS',
    'REDIS_LOGIN_CORVUS',
    'REDIS_TAG_FANS',
    'REDIS_EXPLORE',
    'REDIS_RELATED_TAG',
    'REDIS_HOMEFEED',
    'REDIS_USER_TOPIC_CORVUS',
    'REDIS_MAIN',
    'REDIS_POI_RECOMMEND',
    'REDIS_BOARD_CORVUS',
    'REDIS_BOARD_2_CORVUS',
    'REDIS_HOMEFEED_WHITELIST_USER',
    'REDIS_NOTE_LIST',
    'REDIS_ANDROID_UPDATE',
    'REDIS_NOTE_SCORE',
    'REDIS_CONFIG',
    'REDIS_OPS_BLACKLIST',
    'REDIS_NOTE_CACHE',
    'REDIS_TAG_CACHE',
    'REDIS_TAG_CACHE_CORVUS',
    'REDIS_SEARCH_CACHE',
    'REDIS_SUMMARY2017',
    'REDIS_ADS_SEM',
    'REDIS_MKT_SEM',
    'REDIS_WXMP_QRCODE',
    'REDIS_WXMP_PUSH',
    'REDIS_POI_LIST',
    'SNS_RABBITMQ_HOST',
    'SNS_RABBITMQ_PORT',
    'SNS_RABBITMQ_PRODUCER',
    'SNS_RABBITMQ_PASSWORD',
    'SNS_RABBITMQ_EXCHANGE',
    'QA_RABBITMQ_VHOST',


    # elasticsearch
    'ELASTICSEARCH_SNS_POI',

    # circuit breaker
    'CB_ENABLED',
    'CB_WINDOW',
    'CB_INTERVAL',
    'CB_MAX_FAIL',
    'CB_OPEN_TIME',
    'CB_HALF_OPEN_TIME_RATIO',

    # metrics
    'METRICS_ENABLED',
    'METRICS_INFLUXDB_URL',

    # memcache
    'MC_HOST',
    'MC_PORT',
    'MC_HOST_2',
    'MC_PORT_2',
    'MC_HOST_3',
    'MC_PORT_3',
    'CACHE_INSTRUMENT',

    # Qcloud Image相关的配置
    'QCLOUD_IMAGE_APPID',
    'QCLOUD_IMAGE_SECRET_ID',
    'QCLOUD_IMAGE_SECRET_KEY',
    'QCLOUD_IMAGE_VERIFY_APPID',
    'QCLOUD_IMAGE_VERIFY_SECRET_ID',
    'QCLOUD_IMAGE_VERIFY_SECRET_KEY',
    'QCLOUD_IMAGE_NOTE_IMAGE_BUCKET',
    'QCLOUD_IMAGE_IDENTIFICATION_IMAGE_BUCKET',
    'QCLOUD_IMAGE_VERIFY_IMAGE_BUCKET',
    'QCLOUD_IMAGE_HOST',
    'QCLOUD_IMAGE_VERIFY_HOST',
    'ALIOSS_NOTE_IMAGE_HOST',
    'ALI_OSS_PUBHOST',
    'ALIOSS_HOST',
    'ALIOSS_ACCESS_ID',
    'ALIOSS_SECRET',
    'ALIOSS_BUCKET',

    # Celery相关的配置
    'CELERY_TIMEZONE',
    'CELERY_IMPORTS',
    'CELERY_BROKER_TRANSPORT',
    'CELERY_ONLINE_BROKER_URL',
    'CELERY_STAGING_BROKER_URL',
    'CELERY_SEND_TASK_SENT_EVENT',
    'CELERY_TASK_SEND_SENT_EVENT',
    'CELERY_TASK_SERIALIZER',
    'CELERY_RESULT_SERIALIZER',
    'CELERY_ACCEPT_CONTENT',
    'CELERY_EXCHANGE_NAME',
    'CELERY_BROKER_CONNECTION_MAX_RETRIES',
    'CELERY_BROKER_TRANSPORT_MAX_RETRIES',

    # Foursquare
    'FOURSQUARE_API_CLIENT_ID',
    'FOURSQUARE_API_CLIENT_SECRET',

    # 新浪微博相关配置.
    'WEIBO_CLIENT_ID',
    'WEIBO_CLIENT_SECRET',
    'WEIBO_CB_URL',

    # facebook proxy
    'FACEBOOK_GRAPHAPI_HTTP_PROXY',

    # Experiment framework config
    'EXP_MONGO_HOST',
    'EXP_MONGO_PORT',
    'EXP_MONGO_DB_NAME',
    'EXP_REDIS_HOST',
    'EXP_REDIS_PORT',
    'EXP_REDIS_DB',
    'EXP_REDIS_PASSWORD',
    'FENGKONG_ANTIFRAUD_IMG_URL',

    # misc
    'CDN_HOST',
    'VIDEO_CDN_HOST',
    'TENCENT_LBS_API_KEY',
    'URL_BASE',
    'HTTPS_URL_BASE',
    'AVATAR_BASE_URL',
    'INTERNAL_URL_BASE',
    'ES_API_HOST',
    'WUKONG_HOST',
    'WUKONG_STAGING_HOST',
    'WUKONG_SCHEDULE_TASK_HOST',
    'LOCAL_FEED_HOST',
    'DOLPHIN_HOST',
    'DOLPHIN_HOST_STAGING',
    'RFS_HOST',
    'RFS_HOST_STAGING',
    'HOMEFEED_LOCATION_HOST',
    'SUSPICIOUS_CHECK_URL',
    'ANTISPAM_HOST',
    'ANTISPAM_ORCA_URL',
    'ANTISPAM_ORCA_SUSPICIOUS_NOTE_URL',
    'ANTISPAM_ORCA_SUSPICIOUS_NOTE_URL_V2',
    'OLD_NOTE_CONTENT_ANTISPAM_URL',
    'QINIU_VIDEO_CDN_HOST',
    'QINIU_WEB_VIDEO_CDN_HOST',
    'QINIU_VIDEO_GIF_CDN_HOST',
    'QINIU_API_HOST',
    'QINIU_MUSIC_CDN_HOST',
    'USER_RECOMMEND_URL',
    'IM_INTERNAL_URL',
    'TAXONOMY_INTERNAL_URL',
    'C2C_URL_BASE',
    'CONFIG_UPDATE_INTERVAL',

    # Android push
    'UMENG_PUSH_APP_KEY',
    'UMENG_PUSH_APP_MASTER_SECRET',
    'MIPUSH_APP_SECRET',
    'MIPUSH_PACKAGE_NAME',

    # Note related note external service
    'NOTE_RELATED_NOTE_EXTERNAL_SERVICE_URL',

    # Note related goods from rec url
    'NOTE_RELATED_GOODS_FROM_REC_URL',

    # Qiniu
    'QINIU_NOTE_VIDEO_BUCKET_NAME',
    'QINIU_NOTE_VIDEO_GIF_BUCKET_NAME',
    'QINIU_NOTE_MUSIC_BUCKET_NAME',
    'QINIU_ACCESS_KEY',
    'QINIU_SECRET_KEY',
    'QINIU_ANTI_LEECH_KEY',

    # weather
    'TMAP_KEY',
    'AMAP_KEY',
    'OPEN_WEATHER_APPID',

    # thrift service
    # rps
    'RPS_HOST',
    'RPS_PORT',
    # rus
    'RUS_HOST',
    'RUS_PORT',
    # rts
    'RTS_HOST',
    'RTS_PORT',

    # rts
    'RTS_HOST',
    'RTS_PORT',

    # rms
    'RMS_HOST',
    'RMS_PORT',

    # rbs
    'RBS_HOST',
    'RBS_PORT',

    # rns
    'RNS_HOST',
    'RNS_PORT',

    # java-rus
    'JAVA_RUS_HOST',
    'JAVA_RUS_PORT',

    # java-rns
    'JAVA_RNS_HOST',
    'JAVA_RNS_PORT',

    # thanos
    'THANOS_HOST',
    'THANOS_PORT',

    # wallet
    'WALLET_HOST',
    'WALLET_PORT',

    # setsuna
    'SETSUNA_HOST',
    'SETSUNA_PORT',

    'JAVA_RMS_HOST',
    'JAVA_RMS_PORT',

    # java-rts
    'JAVA_RTS_HOST',
    'JAVA_RTS_PORT',

    # java-rbs
    'JAVA_RBS_HOST',
    'JAVA_RBS_PORT',

    # cube
    'CUBE_HOST',
    'CUBE_PORT',

    # utmark
    'UT_MARK_HOST',
    'UT_MARK_PORT',

    # utpage
    'UT_PAGE_HOST',
    'UT_PAGE_PORT',

    # rabbitmq
    'MQ_HOST',
    'MQ_PORT',

    # rabbitmq
    'FULISHE_MQ_HOST',
    'FULISHE_MQ_PORT',
    'FULISHE_MQ_PRODUCER',
    'FULISHE_MQ_PRODUCER_PASSWORD',
    'FULISHE_MQ_VHOST',
    'REC_PUSH_MQ_HOST',
    'REC_PUSH_MQ_PORT',
    'REC_PUSH_MQ_CONSUMER',
    'REC_PUSH_MQ_CONSUMER_PASSWORD',
    'REC_PUSH_MQ_VHOST',

    # video feed url
    'VIDEO_FEED_URL',
    'VIDEO_FEED_STAGING_URL',
    'VIDEO_FEED_DOWNGRADE',
    'VIDEO_FEED_EXP_URL',

    # wechat_mp
    'WECAHT_MP_APPID',
    'WECHAT_MP_XHSSC_ACCESS_TOKEN_URL',

    # OAUTH
    'WECHAT_OAUTH_URL',
    'QQ_OAUTH_URL',
    'WEIBO_OAUTH_URL',
    'FACEBOOK_OAUTH_URL',
    'CMCC_QUICK_LOGIN_URL',
    'CMCC_QUICK_LOGIN_APPID_IOS',
    'CMCC_QUICK_LOGIN_APPKEY_IOS',
    'CMCC_QUICK_LOGIN_APPID_ANDROID',
    'CMCC_QUICK_LOGIN_APPKEY_ANDROID',

    # default note static file path
    'DEFAULT_NOTE_STATIC_FILE_PATH',

    # wxmp worldcup2018 static file path
    'WXMP_WORLDCUP2018_STATIC_FILE_PATH',
    'CNY_2019_STATIC_FILE_PATH',

    # poi edit
    'POI_EDIT_DOWNGRADE',
]

r = EnvvarReader(*_envvars)

ENV = HENDRIX_ENV = r.get('HENDRIX_ENV', ENV_PROD)
HENDRIX_INTEGRATION_MODE = INTEGRATION_MODE_COMPONENT
ASURA_CHECK_SIGN = r.get('ASURA_CHECK_SIGN', True)
IN_CONTAINER = r.get_bool('IN_CONTAINER', False)
SENTRY_ENABLED = r.get('SENTRY_ENABLED', False)
SENTRY_DSN = r.get('SENTRY_DSN', '')
CDN_HOST = r.get('CDN_HOST', 'http://127.0.0.1')
VIDEO_CDN_HOST = r.get('VIDEO_CDN_HOST', 'http://video.cdn.xiaohongshu.com')
URL_BASE = r.get('URL_BASE', 'http://www.xiaohongshu.com')
HTTPS_URL_BASE = r.get('HTTPS_URL_BASE', 'https://www.xiaohongshu.com')
AVATAR_BASE_URL = r.get('AVATAR_BASE_URL', 'https://img.xiaohongshu.com/avatar/')
INTERNAL_URL_BASE = r.get('INTERNAL_URL_BASE', 'http://api.int.xiaohongshu.com')
ES_API_HOST = r.get('ES_API_HOST', '')
WUKONG_HOST = r.get('WUKONG_HOST', 'http://api-wukong.int.xiaohongshu.com/_search')
WUKONG_STAGING_HOST = r.get('WUKONG_STAGING_HOST', 'http://search-test03:8080/_search')
WUKONG_SCHEDULE_TASK_HOST = r.get('WUKONG_SCHEDULE_TASK_HOST', 'http://search-wk28:8181/_search')
DOLPHIN_HOST = r.get('DOLPHIN_HOST', 'http://dolphin.int.xiaohongshu.com:2222/')
DOLPHIN_HOST_STAGING = r.get('DOLPHIN_HOST_STAGING', 'http://10.0.5.5:2222/')
LOCAL_FEED_HOST = r.get('LOCAL_FEED_HOST', 'http://localfeed.int.xiaohongshu.com:3663/')
RFS_HOST = r.get('RFS_HOST', 'http://localhost:5555/')
RFS_HOST_STAGING = r.get('RFS_HOST_STAGING', 'http://localhost:5555/')
HOMEFEED_LOCATION_HOST = r.get('HOMEFEED_LOCATION_HOST', 'http://dolphin.int.xiaohongshu.com:2222/api/homefeed_ip_city')
SUSPICIOUS_CHECK_URL = r.get('SUSPICIOUS_CHECK_URL', 'http://security.int.xiaohongshu.com/UgcAntiSpam')  # 违禁词检测.
ANTISPAM_HOST = r.get('ANTISPAM_HOST', '')
ANTISPAM_ORCA_URL = r.get('ANTISPAM_ORCA_URL', '')
ANTISPAM_ORCA_SUSPICIOUS_NOTE_URL = r.get('ANTISPAM_ORCA_SUSPICIOUS_NOTE_URL', '')
ANTISPAM_ORCA_SUSPICIOUS_NOTE_URL_V2 = r.get('ANTISPAM_ORCA_SUSPICIOUS_NOTE_URL_V2', 'http://orca.int.xiaohongshu.com/detect_spam/note')
OLD_NOTE_CONTENT_ANTISPAM_URL = r.get('OLD_NOTE_CONTENT_ANTISPAM_URL', '')
USER_RECOMMEND_URL = r.get('USER_RECOMMEND_URL', '')
IM_INTERNAL_URL = r.get('IM_INTERNAL_URL', 'http://im.int.xiaohongshu.com')
TAXONOMY_INTERNAL_URL = r.get('TAXONOMY_INTERNAL_URL', 'http://taxonomy.int.xiaohongshu.com:2823')
C2C_URL_BASE = r.get('C2C_URL_BASE', 'http://www.tst.xiaohongshu.com')
QINIU_VIDEO_CDN_HOST = r.get('QINIU_VIDEO_CDN_HOST', 'http://v.xiaohongshu.com/')
QINIU_WEB_VIDEO_CDN_HOST = r.get('QINIU_WEB_VIDEO_CDN_HOST', 'http://sa.xiaohongshu.com/')
QINIU_VIDEO_GIF_CDN_HOST = r.get('QINIU_VIDEO_GIF_CDN_HOST', 'http://sg.xiaohongshu.com/')
QINIU_API_HOST = r.get('QINIU_API_HOST', 'https://api.qiniu.com/')
QINIU_MUSIC_CDN_HOST = r.get('QINIU_MUSIC_CDN_HOST', 'https://music.xhscdn.com/')
QCLOUD_IMAGE_APPID = r.get('QCLOUD_IMAGE_APPID', '')
QCLOUD_IMAGE_SECRET_ID = r.get('QCLOUD_IMAGE_SECRET_ID', '')
QCLOUD_IMAGE_SECRET_KEY = r.get('QCLOUD_IMAGE_SECRET_KEY', '')
QCLOUD_IMAGE_VERIFY_APPID = r.get('QCLOUD_IMAGE_VERIFY_APPID', '')
QCLOUD_IMAGE_VERIFY_SECRET_ID = r.get('QCLOUD_IMAGE_VERIFY_SECRET_ID', '')
QCLOUD_IMAGE_VERIFY_SECRET_KEY = r.get('QCLOUD_IMAGE_VERIFY_SECRET_KEY', '  ')
QCLOUD_IMAGE_NOTE_IMAGE_BUCKET = r.get('QCLOUD_IMAGE_NOTE_IMAGE_BUCKET', 'xhsci')
QCLOUD_IMAGE_IDENTIFICATION_IMAGE_BUCKET = r.get('QCLOUD_IMAGE_IDENTIFICATION_IMAGE_BUCKET', 'xhsids')
QCLOUD_IMAGE_VERIFY_IMAGE_BUCKET = r.get('QCLOUD_IMAGE_VERIFY_IMAGE_BUCKET', 'redverify')
QCLOUD_IMAGE_HOST = r.get('QCLOUD_IMAGE_HOST', 'http://ci.xiaohongshu.com/')
QCLOUD_IMAGE_VERIFY_HOST = r.get('QCLOUD_IMAGE_VERIFY_HOST', 'http://redverify-1251524319.image.myqcloud.com/')
ALIOSS_NOTE_IMAGE_HOST = r.get('ALIOSS_NOTE_IMAGE_HOST', 'http://o4.xiaohongshu.com/')
ALI_OSS_PUBHOST = r.get('ALI_OSS_PUBHOST', 'o4.xiaohongshu.com')
ALIOSS_HOST = r.get('ALIOSS_HOST', '')
ALIOSS_ACCESS_ID = r.get('ALIOSS_ACCESS_ID', '')
ALIOSS_SECRET = r.get('ALIOSS_SECRET', '')
ALIOSS_BUCKET = r.get('ALIOSS_BUCKET', '')
TENCENT_LBS_API_KEY = r.get('TENCENT_LBS_API_KEY', 'I2GBZ-CW43F-Y5OJB-NTEUL-PEES6-NNBL2')
FOURSQUARE_API_CLIENT_ID = r.get('FOURSQUARE_API_CLIENT_ID', 'K1ABCMKIDMUYVIMJKDMDN44O5EII0X0FQGMKYG3ZICUANV4F')
FOURSQUARE_API_CLIENT_SECRET = r.get('FOURSQUARE_API_CLIENT_SECRET', '5B200ZGAD10OFUFI5MHLHYUXPE0EG2BHFYBN011IBYYUGX00')
WECHAT_OAUTH_URL = r.get('WECHAT_OAUTH_URL', 'https://api.weixin.qq.com/sns/userinfo')
QQ_OAUTH_URL = r.get('QQ_OAUTH_URL', 'https://graph.qq.com/oauth2.0/me')
WEIBO_OAUTH_URL = r.get('WEIBO_OAUTH_URL', 'https://api.weibo.com/oauth2/get_token_info')
FACEBOOK_OAUTH_URL = r.get('FACEBOOK_OAUTH_URL', 'https://graph.facebook.com/v2.12/me')
CMCC_QUICK_LOGIN_URL = r.get('CMCC_QUICK_LOGIN_URL', 'https://www.cmpassport.com/unisdk/rsapi/loginTokenValidate')

WEIBO_CLIENT_ID = r.get('WEIBO_CLIENT_ID', '785270868')
WEIBO_CLIENT_SECRET = r.get('WEIBO_CLIENT_SECRET', 'c2bd55e4c92d2e76f612d3784e68bfe7')
WEIBO_CB_URL = r.get('WEIBO_CB_URL', 'http://www.xiaohongshu.com/cb_weibo')
FACEBOOK_GRAPHAPI_HTTP_PROXY = r.get('FACEBOOK_GRAPHAPI_HTTP_PROXY', 'http://10.1.0.107:3128')
WECAHT_MP_APPID = r.get('WECAHT_MP_APPID', 'wxffc08ac7df482a27')
WECHAT_MP_XHSSC_ACCESS_TOKEN_URL = r.get('WECHAT_MP_XHSSC_ACCESS_TOKEN_URL', 'https://odin.xiaohongshu.com/api/odin/common/mp_token')
CMCC_QUICK_LOGIN_APPID_IOS = r.get('CMCC_QUICK_LOGIN_APPID_IOS', '300011856675')
CMCC_QUICK_LOGIN_APPKEY_IOS = r.get('CMCC_QUICK_LOGIN_APPKEY_IOS', '7F96CFF130233A1A8213D7F0B62F5C48')
CMCC_QUICK_LOGIN_APPID_ANDROID = r.get('CMCC_QUICK_LOGIN_APPID_ANDROID', '300011857041')
CMCC_QUICK_LOGIN_APPKEY_ANDROID = r.get('CMCC_QUICK_LOGIN_APPKEY_ANDROID', '2B585856BC8DBDB15B3F1C3CE279602C')

CELERY_TIMEZONE = r.get('CELERY_TIMEZONE', 'Asia/Shanghai')
CELERY_IMPORTS = r.get('CELERY_IMPORTS', 'asura.bgtask.tasks')
BROKER_TRANSPORT = r.get('CELERY_BROKER_TRANSPORT', 'redis')
CELERY_ONLINE_BROKER_URL = r.get('CELERY_ONLINE_BROKER_URL', 'redis://localhost:6379/0')
CELERY_STAGING_BROKER_URL = r.get('CELERY_STAGING_BROKER_URL', 'redis://localhost:6379/0')
CELERY_SEND_TASK_SENT_EVENT = r.get('CELERY_SEND_TASK_SENT_EVENT', False)
CELERY_TASK_SEND_SENT_EVENT = r.get('CELERY_TASK_SEND_SENT_EVENT', False)
CELERY_TASK_SERIALIZER = r.get('CELERY_TASK_SERIALIZER', 'pickle')
CELERY_RESULT_SERIALIZER = r.get('CELERY_RESULT_SERIALIZER', 'json')
CELERY_ACCEPT_CONTENT = r.get('CELERY_ACCEPT_CONTENT', ['json', 'pickle'])
CELERY_EXCHANGE_NAME = r.get('CELERY_EXCHANGE_NAME', 'sns.asura')
BROKER_CONNECTION_MAX_RETRIES = r.get('CELERY_BROKER_CONNECTION_MAX_RETRIES', 5)
BROKER_TRANSPORT_OPTIONS = {
    'max_retries': r.get('CELERY_BROKER_TRANSPORT_MAX_RETRIES', 5)
}

EXP_MONGO_HOST = r.get('EXP_MONGO_HOST', 'localhost')
EXP_MONGO_PORT = r.get('EXP_MONGO_PORT', 27017)
EXP_MONGO_DB_NAME = r.get('EXP_MONGO_DB_NAME', 'db_prod')
EXP_REDIS_HOST = r.get('EXP_REDIS_HOST', 'localhost')
EXP_REDIS_PORT = r.get('EXP_REDIS_PORT', 6379)
EXP_REDIS_DB = r.get('EXP_REDIS_DB', 0)
EXP_REDIS_PASSWORD = r.get('EXP_REDIS_PASSWORD', None)
FENGKONG_ANTIFRAUD_IMG_URL = r.get('FENGKONG_ANTIFRAUD_IMG_URL', 'http://img-api-sh.fengkongcloud.com/v2/saas/anti_fraud/img')

UMENG_PUSH_APP_KEY = r.get('UMENG_PUSH_APP_KEY', '')
UMENG_PUSH_APP_MASTER_SECRET = r.get('UMENG_PUSH_APP_MASTER_SECRET', '')
MIPUSH_APP_SECRET = r.get('MIPUSH_APP_SECRET', '')
MIPUSH_PACKAGE_NAME = r.get('MIPUSH_PACKAGE_NAME', '')

NOTE_RELATED_NOTE_EXTERNAL_SERVICE_URL = r.get('NOTE_RELATED_NOTE_EXTERNAL_SERVICE_URL', '')
NOTE_RELATED_GOODS_FROM_REC_URL = r.get('NOTE_RELATED_GOODS_FROM_REC_URL', '')

QINIU_NOTE_VIDEO_BUCKET_NAME = r.get('QINIU_NOTE_VIDEO_BUCKET_NAME', 'note-video')
QINIU_NOTE_VIDEO_GIF_BUCKET_NAME = r.get('QINIU_NOTE_VIDEO_GIF_BUCKET_NAME', 'note-video-gif')
QINIU_NOTE_MUSIC_BUCKET_NAME = r.get('QINIU_NOTE_MUSIC_BUCKET_NAME', 'note-music')
QINIU_ACCESS_KEY = r.get('QINIU_ACCESS_KEY', '')
QINIU_SECRET_KEY = r.get('QINIU_SECRET_KEY', '')
QINIU_ANTI_LEECH_KEY = r.get('QINIU_ANTI_LEECH_KEY', '')

TMAP_KEY = r.get('TMAP_KEY', '')
AMAP_KEY = r.get('AMAP_KEY', ''),
OPEN_WEATHER_APPID = r.get('OPEN_WEATHER_APPID', ''),

VIDEO_FEED_URL = r.get('VIDEO_FEED_URL', '')
VIDEO_FEED_STAGING_URL = r.get('VIDEO_FEED_STAGING_URL', '')
VIDEO_FEED_DOWNGRADE = r.get('VIDEO_FEED_DOWNGRADE') not in (None, '', '0', 'False')
VIDEO_FEED_EXP_URL = r.get('VIDEO_FEED_EXP_URL', '')

DEFAULT_NOTE_STATIC_FILE_PATH = r.get('DEFAULT_NOTE_STATIC_FILE_PATH', '/data/sns.asura/static/default_note')
WXMP_WORLDCUP2018_STATIC_FILE_PATH = r.get('WXMP_WORLDCUP2018_STATIC_FILE_PATH', '/data/sns.asura/static/wxmp_worldcup2018')
CNY_2019_STATIC_FILE_PATH = r.get('CNY_2019_STATIC_FILE_PATH', '/data/sns.asura/static/cny2019')
DEFAULT_USER_BANNER_IMAGE = 'http://s4.xiaohongshu.com/static/huati/6d46171e066c82db069e0978716269b9.jpg'
CONFIG_UPDATE_INTERVAL = r.get('CONFIG_UPDATE_INTERVAL', 10)

POI_EDIT_DOWNGRADE = r.get('POI_EDIT_DOWNGRADE') not in (None, '', '0', 'False')


def _get_db_setting(envvar, db, alias=None):
    local_db_url = 'mongodb://localhost:27017'
    default = {
        'host': '/'.join([local_db_url, db]),
    }
    if alias:
        default.update({'alias': alias})
    url = r.get_json(envvar, default)
    return url


DB_SETTINGS = {
    'db_prod': _get_db_setting('DB_PROD', 'db_prod'),
    'db_athena': _get_db_setting('DB_ATHENA', 'db_athena', 'db_athena'),
    'db_prod_6001': _get_db_setting('DB_PROD_6001', 'db_prod', 'db_prod_6001'),
    'db_prod_6003': _get_db_setting('DB_PROD_6003', 'db_prod', 'db_prod_6003'),
    'sns_message': _get_db_setting('DB_SNS_MESSAGE', 'sns_message', 'sns_message'),
    'sns_note': _get_db_setting('DB_SNS_NOTE', 'sns_note', 'sns_note'),
    'sns_user_relationship': _get_db_setting('DB_SNS_USER_RELATIONSHIP', 'sns_user_relationship', 'sns_user_relationship'),
    'poi': _get_db_setting('DB_POI', 'poi', 'poi'),
    'poi_new': _get_db_setting('DB_POI_NEW', 'poi', 'poi_new'),
    'board': _get_db_setting('DB_BOARD', 'board', 'board'),
    'db_sns_1': _get_db_setting('DB_SNS_1', 'db_sns_1', 'db_sns_1'),
    'db_sns_1_new': _get_db_setting('DB_SNS_1_NEW', 'db_sns_1', 'db_sns_1_new'),
    'db_sns_1_spvnote': _get_db_setting('DB_SNS_1_SPVNOTE', 'db_sns_1', 'db_sns_1_spvnote'),
    'activity': _get_db_setting('DB_ACTIVITY', 'activity', 'activity'),
    'user': _get_db_setting('DB_USER', 'user', 'user'),

    # New mongodb 3.2 cluster
    'sns_note_new': _get_db_setting('DB_SNS_NOTE_NEW', 'sns_note', 'sns_note_new'),
    'sns_note_6003': _get_db_setting('DB_SNS_NOTE_6003', 'sns_note', 'sns_note_6003'),
    'sns_message_new': _get_db_setting('DB_SNS_MESSAGE_NEW', 'sns_message', 'sns_message_new'),
    'activity_6003': _get_db_setting('DB_ACTIVITY_6003', 'activity', 'activity_6003'),
    'activity_6004': _get_db_setting('DB_ACTIVITY_6004', 'activity', 'activity_6004'),
    'user_new': _get_db_setting('DB_USER_NEW', 'user', 'user_new'),
    'sns_user_relationship_6002': _get_db_setting('DB_SNS_USER_RELATIONSHIP_6002', 'sns_user_relationship', 'sns_user_relationship_6002'),
    'board_new': _get_db_setting('DB_BOARD_NEW', 'board', 'board_new'),
    'page': _get_db_setting('DB_PAGE', 'page', 'page'),
    'idol_producer': _get_db_setting('DB_IDOL_PRODUCER', 'idol_producer', 'idol_producer'),
    'ads': _get_db_setting('DB_ADS', 'ads', 'ads'),
    'squad_page': _get_db_setting('DB_SQUAD_PAGE', 'squad_page', 'squad_page'),
    'new_user_feed': _get_db_setting('DB_NEW_USER_FEED', 'snapshot', 'new_user_feed'),
    'db_prod_30006': _get_db_setting('DB_PROD_30006', 'db_prod', 'db_prod_30006'),
    'data_sem': _get_db_setting('DB_DATA_SEM', 'snapshot', 'data_sem'),
    'sns_wxmp_activity': _get_db_setting('DB_SNS_WXMP_ACTIVITY', 'sns_wxmp_activity', 'sns_wxmp_activity'),
}

CACHE_SETTINGS = {
    'ocm': {
        'url': 'memcached://{}:{}'.format(
            r.get('MC_HOST', '127.0.0.1'), r.get_int('MC_PORT', 11211)),
        'max_pool_size': 100,
        'connect_timeout': 1.0,
        'timeout': 0.1,
        'instrument': r.get_bool('CACHE_INSTRUMENT')
    },
    'ocm_2': {
        'url': 'memcached://{}:{}'.format(
            r.get('MC_HOST_2', '127.0.0.1'), r.get_int('MC_PORT_2', 11211)),
        'max_pool_size': 100,
        'connect_timeout': 1.0,
        'timeout': 0.1,
        'instrument': r.get_bool('CACHE_INSTRUMENT')
    },
    'ocm_3': {
        'url': 'memcached://{}:{}'.format(
            r.get('MC_HOST_3', '127.0.0.1'), r.get_int('MC_PORT_3', 11211)),
        'max_pool_size': 100,
        'connect_timeout': 1.0,
        'timeout': 0.1,
        'instrument': r.get_bool('CACHE_INSTRUMENT')
    },
}
DEFAULT_REDIS_SETTING = {
    'password': '',
    'host': '127.0.0.1',
    'port': 6379,
    'db': 0,
}
REDIS_SETTINGS = {
    'sns_tag_like': r.get_json('REDIS_SNS_TAG_LIKE', DEFAULT_REDIS_SETTING),
    'sns_tag_like_corvus': r.get_json('REDIS_SNS_TAG_LIKE_CORVUS', DEFAULT_REDIS_SETTING),
    'note_like_corvus': r.get_json('REDIS_NOTE_LIKE_CORVUS', DEFAULT_REDIS_SETTING),
    'note_view_corvus': r.get_json('REDIS_NOTE_VIEW_CORVUS', DEFAULT_REDIS_SETTING),
    'user_msg': r.get_json('REDIS_USER_MSG', DEFAULT_REDIS_SETTING),
    'user_follow': r.get_json('REDIS_USER_FOLLOW', DEFAULT_REDIS_SETTING),
    'user_follow_corvus': r.get_json('REDIS_USER_FOLLOW_CORVUS', DEFAULT_REDIS_SETTING),
    'blocked_user_corvus': r.get_json('REDIS_BLOCKED_USER_CORVUS', DEFAULT_REDIS_SETTING),
    'user_fans_corvus': r.get_json('REDIS_USER_FANS_CORVUS', DEFAULT_REDIS_SETTING),
    'inter_user': r.get_json('REDIS_INTER_USER', DEFAULT_REDIS_SETTING),
    'user_info_corvus': r.get_json('REDIS_USER_INFO_CORVUS', DEFAULT_REDIS_SETTING),
    'user_session_corvus': r.get_json('REDIS_USER_SESSION_CORVUS', DEFAULT_REDIS_SETTING),
    'user_cache_corvus': r.get_json('REDIS_USER_CACHE_CORVUS', DEFAULT_REDIS_SETTING),
    'featured_page_info': r.get_json('REDIS_FEATURED_PAGE_INFO', DEFAULT_REDIS_SETTING),
    'note_view': r.get_json('REDIS_NOTE_VIEW', DEFAULT_REDIS_SETTING),
    'throne': r.get_json('REDIS_THRONE', DEFAULT_REDIS_SETTING),
    'user_recommend': r.get_json('REDIS_USER_RECOMMEND', DEFAULT_REDIS_SETTING),
    'note_red_packet': r.get_json('REDIS_NOTE_RED_PACKET', DEFAULT_REDIS_SETTING),
    'peak_note': r.get_json('REDIS_PEAK_NOTE', DEFAULT_REDIS_SETTING),
    'message_aggregation': r.get_json('REDIS_MESSAGE_AGGREGATION', DEFAULT_REDIS_SETTING),
    'comment_corvus': r.get_json('REDIS_COMMENT_CORVUS', DEFAULT_REDIS_SETTING),
    'login_corvus': r.get_json('REDIS_LOGIN_CORVUS', DEFAULT_REDIS_SETTING),
    'tag_fans': r.get_json('REDIS_TAG_FANS', DEFAULT_REDIS_SETTING),
    'explore': r.get_json('REDIS_EXPLORE', DEFAULT_REDIS_SETTING),
    'related_tag': r.get_json('REDIS_RELATED_TAG', DEFAULT_REDIS_SETTING),
    'homefeed': r.get_json('REDIS_HOMEFEED', DEFAULT_REDIS_SETTING),
    'user_topic': r.get_json('REDIS_USER_TOPIC_CORVUS', DEFAULT_REDIS_SETTING),
    'main': r.get_json('REDIS_MAIN', DEFAULT_REDIS_SETTING),
    'poi_recommend': r.get_json('REDIS_POI_RECOMMEND', DEFAULT_REDIS_SETTING),
    'board_corvus': r.get_json('REDIS_BOARD_CORVUS', DEFAULT_REDIS_SETTING),
    'board2_corvus': r.get_json('REDIS_BOARD_2_CORVUS', DEFAULT_REDIS_SETTING),
    'whitelist_user': r.get_json('REDIS_HOMEFEED_WHITELIST_USER', DEFAULT_REDIS_SETTING),
    'note_list': r.get_json('REDIS_NOTE_LIST', DEFAULT_REDIS_SETTING),
    'android_update': r.get_json('REDIS_ANDROID_UPDATE', DEFAULT_REDIS_SETTING),
    'note_score': r.get_json('REDIS_NOTE_SCORE', DEFAULT_REDIS_SETTING),
    'config': r.get_json('REDIS_CONFIG', DEFAULT_REDIS_SETTING),
    'ops_blacklist': r.get_json('REDIS_OPS_BLACKLIST', DEFAULT_REDIS_SETTING),
    'note_cache': r.get_json('REDIS_NOTE_CACHE', DEFAULT_REDIS_SETTING),
    'tag_cache': r.get_json('REDIS_TAG_CACHE', DEFAULT_REDIS_SETTING),
    'tag_cache_corvus': r.get_json('REDIS_TAG_CACHE_CORVUS', DEFAULT_REDIS_SETTING),
    'search_cache': r.get_json('REDIS_SEARCH_CACHE', DEFAULT_REDIS_SETTING),
    'summary2017': r.get_json('REDIS_SUMMARY2017', DEFAULT_REDIS_SETTING),
    'ads_sem': r.get_json('REDIS_ADS_SEM', DEFAULT_REDIS_SETTING),
    'mkt_sem': r.get_json('REDIS_MKT_SEM', DEFAULT_REDIS_SETTING),
    'wxmp_qrcode': r.get_json('REDIS_WXMP_QRCODE', DEFAULT_REDIS_SETTING),
    'wxmp_push': r.get_json('REDIS_WXMP_PUSH', DEFAULT_REDIS_SETTING),
    'poi_list': r.get_json('REDIS_POI_LIST', DEFAULT_REDIS_SETTING),
}

ELASTICSEARCH_SETTINGS = {
    'sns_poi': r.get_json('ELASTICSEARCH_SNS_POI', [{
        'host': 'localhost',
    }]),
}

METRICS_ENABLED = r.get('METRICS_ENABLED', True)
METRICS_INFLUXDB_URL = r.get('METRICS_INFLUXDB_URL', 'influxdb://localhost:8086')
METRICS_SCHEMAS = {
    'asura': {
        '_srv': 'influxdb',
        '_opts': {
            'url': METRICS_INFLUXDB_URL,
            'db_name': 'asura',
            'udp_enabled': True,
            'udp_port': 8099,
        },
        'cache.op': {
            'tags': [
                'op',
                'hostname',
                'server',
                'api',
                'timeout',
                'exc',
                'retry',
            ],
            'fields': [
                'value',
                'key',
                'rid',
            ],
        },
        'cache.conn': {
            'tags': [
                'server',
                'used',
                'hostname',
            ],
            'fields': [
                'value',
            ],
            'precision': 's',
        },
        'cache_ops': {  # To be DEPRECATED
            'tags': [
                'op',
                'hostname',
                'server',
                'endpoint',
                'platform',
            ],
            'fields': [
                'value',
                'key',
                'rid',
            ]
        },
        'cache_client_pool': {  # To be DEPRECATED
            'tags': [
                'server',
                'used',
                'hostname',
            ],
            'fields': [
                'value',
            ],
            'precision': 's',
        },
        'thrift.connection.ops': {
            'tags': [
                'hostname',
                'endpoint',
                'service_name',
            ],
            'fields': [
                'value',
            ],
        },
        'thrift.connection.pool': {
            'tags': [
                'used',
                'hostname',
                'service_name',
            ],
            'fields': [
                'value',
            ],
            'precision': 's',
        },
        'mongo.ops': {
            'tags': [
                'ns',
                'op',
                'ok',
                'hostname',
            ],
            'fields': [
                'value',
                'rid',
                'req_id',
                'op_id',
            ]
        },
        'api_calls': {
            'tags': [
                'endpoint',
                'hostname',
                'exc',
                'success',
                'platform',
            ],
            'fields': [
                'value',
                'rid',
            ]
        },
        'api.circuit_breaker': {
            'tags': [
                'endpoint',
                'hostname',
            ],
            'fields': [
                'value',
                'rid',
            ]
        },
        'api.circuit_breaker.event': {
            'tags': [
                'endpoint',
                'event',
                'hostname',
            ],
            'fields': [
                'value',
            ]
        },
        'search_service': {
            'tags': [
                'hostname',
                'server',
                'search_category',
                'success',
            ],
            'fields': [
                'value',
            ],
        },
        'homefeed_service': {
            'tags': [
                'hostname',
                'server',
                'path',
                'category',
                'generate',
                'success',
            ],
            'fields': [
                'value',
            ],
        },
        'rfs_service': {
            'tags': [
                'hostname',
                'server',
                'path',
                'generate',
                'success',
            ],
            'fields': [
                'value',
            ],
        },
        'followfeed_result': {
            'tags': [
                'hostname',
                'cursor_score',
                'user_id',
                'rfs_version',
                'result_count'
            ],
            'fields': [
                'value',
            ],
        },
        'related_note_service': {
            'tags': [
                'hostname',
                'server',
                'category',
                'success',
            ],
            'fields': [
                'value',
            ],
        },
        'fls_internal_api_call': {
            'tags': [
                'hostname',
                'category',
                'success',
            ],
            'fields': [
                'value',
            ],
        },
        'sms_service': {
            'tags': [
                'hostname',
                'vendor',
                'success',
            ],
            'fields': [
                'value',
            ],
        },
        'redis.conn': {
            'tags': [
                'used',
                'hostname',
                'server',
                'service_name',
            ],
            'fields': [
                'value',
            ],
            'precision': 's',
        },
        'redis.op': {
            'tags': [
                'op',
                'hostname',
                'server',
                'api',
                'exc',
            ],
            'fields': [
                'value',
                'key',
                'rid',
            ],
        },
        'note_related_goods_from_rec': {
            'tags': [
                'hostname',
                'success',
            ],
            'fields': [
                'value',
            ],
        },
    },
}

CB_ENABLED = r.get_bool('CB_ENABLED', True)
CB_WINDOW = r.get_int('CB_WINDOW', 20 * 1000)
CB_INTERVAL = r.get_int('CB_INTERVAL', 1000)
CB_MAX_FAIL = r.get_int('CB_MAX_FAIL', 3)
CB_OPEN_TIME = r.get_int('CB_OPEN_TIME', 20 * 1000)
CB_HALF_OPEN_TIME_RATIO = r.get_float('CB_HALF_OPEN_TIME_RATIO', 2.0)

RPS_HOST = r.get('RPS_HOST', '127.0.0.1')
RPS_PORT = r.get_int('RPS_PORT', 4502)

RUS_HOST = r.get('RUS_HOST', '127.0.0.1')
RUS_PORT = r.get_int('RUS_PORT', 4504)

RTS_HOST = r.get('RTS_HOST', '127.0.0.1')
RTS_PORT = r.get_int('RTS_PORT', 4510)

RMS_HOST = r.get('RMS_HOST', '127.0.0.1')
RMS_PORT = r.get_int('RMS_PORT', 4512)

RBS_HOST = r.get('RBS_HOST', '127.0.0.1')
RBS_PORT = r.get_int('RBS_PORT', 4514)

RNS_HOST = r.get('RNS_HOST', '127.0.0.1')
RNS_PORT = r.get_int('RNS_PORT', 4516)

JAVA_RUS_HOST = r.get('JAVA_RUS_HOST', '127.0.0.1')
JAVA_RUS_PORT = r.get_int('JAVA_RUS_PORT', 4241)

JAVA_RNS_HOST = r.get('JAVA_RNS_HOST', '127.0.0.1')
JAVA_RNS_PORT = r.get_int('JAVA_RNS_PORT', 4245)

SETSUNA_HOST = r.get('SETSUNA_HOST', '127.0.0.1')
SETSUNA_PORT = r.get_int('SETSUNA_PORT', 4248)

WALLET_HOST = r.get('WALLET_HOST', '127.0.0.1')
WALLET_PORT = r.get_int('WALLET_PORT', 4249)

THANOS_HOST = r.get('THANOS_HOST', '127.0.0.1')
THANOS_PORT = r.get_int('THANOS_PORT', 4247)

JAVA_RMS_HOST = r.get('JAVA_RMS_HOST', '127.0.0.1')
JAVA_RMS_PORT = r.get_int('JAVA_RMS_PORT', 4243)

JAVA_RTS_HOST = r.get('JAVA_RTS_HOST', '127.0.0.1')
JAVA_RTS_PORT = r.get_int('JAVA_RTS_PORT', 4242)

JAVA_RBS_HOST = r.get('JAVA_RBS_HOST', '127.0.0.1')
JAVA_RBS_PORT = r.get_int('JAVA_RBS_PORT', 4244)

CUBE_HOST = r.get('CUBE_HOST', '127.0.0.1')
CUBE_PORT = r.get_int('CUBE_PORT', 4246)

UT_MARK_HOST = r.get('UT_MARK_HOST', '127.0.0.1')
UT_MARK_PORT = r.get_int('UT_MARK_PORT', 4275)

UT_PAGE_HOST = r.get('UT_PAGE_HOST', '127.0.0.1')
UT_PAGE_PORT = r.get_int('UT_PAGE_PORT', 4274)

MQ_HOST = r.get('MQ_HOST', '127.0.0.1')
MQ_PORT = r.get_int('MQ_PORT', 5670)

FULISHE_MQ_HOST = r.get('FULISHE_MQ_HOST', 'fls-dev')
FULISHE_MQ_PORT = r.get_int('FULISHE_MQ_PORT', 5670)
FULISHE_MQ_VHOST = r.get('FULISHE_MQ_VHOST', 'test')

FULISHE_MQ_PRODUCER = r.get('FULISHE_MQ_PRODUCER', 'qa')
FULISHE_MQ_PRODUCER_PASSWORD = r.get('FULISHE_MQ_PRODUCER_PASSWORD', 'red-qa')

REC_PUSH_MQ_HOST = r.get('REC_PUSH_MQ_HOST', 'rec-push-mq')
REC_PUSH_MQ_PORT = r.get_int('REC_PUSH_MQ_PORT', 5670)
REC_PUSH_MQ_VHOST = r.get('REC_PUSH_MQ_VHOST', 'online_push')

REC_PUSH_MQ_CONSUMER = r.get('REC_PUSH_MQ_CONSUMER', 'consumer')
REC_PUSH_MQ_CONSUMER_PASSWORD = r.get('REC_PUSH_MQ_CONSUMER_PASSWORD', '1FkbOKUApTUL3IO3')

SNS_RABBITMQ_HOST = r.get('SNS_RABBITMQ_HOST', 'sns-rabbitmq.int.xiaohongshu.com')
SNS_RABBITMQ_PORT = r.get('SNS_RABBITMQ_PORT', 5670)
SNS_RABBITMQ_PRODUCER = r.get('SNS_RABBITMQ_PRODUCER', 'producer')
SNS_RABBITMQ_PASSWORD = r.get('SNS_RABBITMQ_PASSWORD', '49898228-24cf-11e7-a8a6-acbc329430af')

QA_RABBITMQ_EXCHANGE = r.get('SNS_RABBITMQ_EXCHANGE', 'qathemis_exchange')
QA_RABBITMQ_VHOST = r.get('QA_RABBITMQ_VHOST', 'qathemis')


PASSWORD_LOGIN_WHITELIST = [
    '593974fc5e87e71ee9242f0d',
    '58596a6b5e87e752c0634404',
    '549e414e2e1d935057a7f95f',
    '58b4fbdc6a6a690e3f7653b6',
    '5a1697d04eacab4f1cc5749e',             # 全球选
    '597ed5f250c4b4507274c092',             # 保健FM

    # 《创造101》综艺节目的选手们
    # 辣鸡OPPO公司只给选手配40台手机导致小姐姐们不方便用验证码登录小红书
    '5ad47bb580008671255c6914',
    '5ad47bb580008671255c6915',
    '5ad47bb580008671255c6916',
    '5ad47bb580008671255c6917',
    '5ad47bb580008671255c6918',
    '5ad47bb580008671255c6919',
    '5ad47bb580008671255c691a',
    '5ad47bb580008671255c691b',
    '5aceead7e8ac2b2831d4b29c',
    '56965e9084edcd54914606b7',
    '5acf3abce8ac2b58e215b46a',
    '5ad47bb580008671255c691c',
    '5ad47bb580008671255c691d',
    '59456de55e87e7797d9da706',
    '5ad47bb580008671255c691e',
    '5ad47bb580008671255c691f',
    '5ad47bb580008671255c6920',
    '5ad47bb580008671255c6921',
    '5ad47bb580008671255c6922',
    '5a3292c7e8ac2b6d6ac93f09',
    '5ad47bb580008671255c6923',
    '58e354585e87e71b73e96c24',
    '5ad47bb580008671255c6924',
    '5a7d2f12e8ac2b6dae88d695',
    '59e4a90b4eacab5abb7aad5c',
    '5ad47bb580008671255c6925',
    '5ad47bb580008671255c6926',
    '5ad47bb580008671255c6927',
    '5ad47bb580008671255c6928',
    '5ad47bb580008671255c6929',
    '5ad47bb580008671255c692a',
    '5ad47bb580008671255c692b',
    '5ad47bb580008671255c692c',
    '5ad47bb580008671255c692d',
    '5ad47bb580008671255c692e',
    '5ad47bb580008671255c692f',
    '5ad47bb580008671255c6930',
    '54e89717d39ea22258501925',
    '5ad47bb680008671255c6931',
    '5ad47bb680008671255c6932',
    '5ad47bb680008671255c6933',
    '5ad47bb680008671255c6934',
    '5ad47bb680008671255c6935',
    '5a8a87024eacab3b6d75d678',
    '5ad47bb680008671255c6936',
    '5ad47bb680008671255c6937',
    '5ad47bb680008671255c6938',
    '5ad47bb680008671255c6939',
    '5ad47bb680008671255c693a',
    '5ad47bb680008671255c693b',
    '5691297d84edcd7bfec78bba',
    '5ad47bb680008671255c693c',
    '5ad47bb680008671255c693d',
    '58d10a2782ec3904d49f6306',
    '5ad47bb680008671255c693e',
    '5ad47bb680008671255c693f',
    '5ad47bb680008671255c6940',
    '5ad47bb680008671255c6941',
    '5ad47bb680008671255c6942',
    '5ad47bb680008671255c6943',
    '5ad47bb680008671255c6944',
    '5ad47bb680008671255c6945',
    '5aceb8d5e8ac2b1e202e843d',
    '5ad47bb680008671255c6946',
    '5ad47bb680008671255c6947',
    '5ad47bb680008671255c6948',
    '5ad47bb680008671255c6949',
    '5ad0bea711be100a197b8cce',
    '54869a95d6e4a91c92db3fe5',
    '5ad47bb680008671255c694a',
    '56dd8c0f84edcd3f08991b47',
    '5ad47bb680008671255c694b',
    '5ad47bb680008671255c694c',
    '5ad47bb680008671255c694d',
    '5ad47bb680008671255c694e',
    '5ad47bb680008671255c694f',
    '5837b4faa9b2ed4a05f82948',
    '5ad47bb680008671255c6950',
    '5a9bc55ce8ac2b7a7c38f053',
    '5ad47bb680008671255c6951',
    '5ad47bb680008671255c6952',
    '5ad47bb680008671255c6953',
    '59f7e73211be1062f5ac6895',
    '5599bbbd3397db5ef49f8af8',
    '5604a828c2bdeb722bc8f23f',
    '5ad47bb780008671255c6954',
    '5ad47bb780008671255c6955',
    '54259789d6e4a923e46cbb8e',
    '59bfb99482ec3905e30d29c1',
    '54c6489c2e1d934695f8d2dd',
    '5ad47bb780008671255c6956',
    '55ca10f0a75c9516ad61e4fa',
    '5ad058174eacab60be8910f4',
    '5ac46d37e8ac2b533cfc8044',
    '5a0700cb11be1075b70a0300',
    '5ad47bb780008671255c6957',
    '5a3f0005e8ac2b535a179e3f',
    '5ae441568000861432072461',
    '56e52bbf84edcd139a6cf6d0',
    '5ad063144eacab6b77765808',
    '5ad064254eacab6b77765873',

    # QA组给外包团队用的测试号
    '561e84b308039441de1be379',
    '59db4ea2de5fb4044a630492',
    '59db4ef044363b45d7c7aac9',
    '59db4ef020e88f53bbf0fc21',
    '59db4ef120e88f7aadd29513',
    '59db4ef251783a06b6017445',
    '59db4ef2de5fb40543ee98fb',
    '59db4ef3de5fb47b1c413429',
    '59db4ef351783a5f1a4fd368',
    '59db4ef420e88f5839cda526',
    '59db4ef444363b4e85d9f993',
    '59db4ef520e88f7aadd29516',
    '59db4fc444363b5037214433',
    '59db4fc5de5fb403cd014dd0',
    '59db4fc56eea88596ab65a67',
    '59db4fc620e88f591bc38eba',
    '59db4fc751783a0f51b53da3',
    '59db4fc76eea8859603ee047',
    '59db4fc851783a095fc78994',
    '59db4fc844363b4e85d9fa82',
    '59db4fc920e88f591bc38ebe',
    '59db4fc9de5fb4064f6561cb',
    '5b17add44eacab1107ddefcb',
    '5b17add611be100868f9a318',
    '5b17add7e8ac2b24771dcd40',
    '5b17add811be100868f9a31c',
    '5b17add9e8ac2b21c31ff275',
    '5b17addb4eacab101902edb1',
    '5b17addce8ac2b24771dcd43',
    '5b17addd11be107b322cbdba',
    '5b17adde11be107ea127e5e5',
    '5b17ade14eacab101902edb4',
    '5b17ade211be107ea127e5ea',
    '5b17ade311be107ea127e5ed',
    '5b17ade44eacab7456d6de7d',
    '5b17ade6e8ac2b21c31ff278',
    '5b17ade711be1008995b1ccd',
    '5b17ade8e8ac2b21c31ff27b',
    '5b17ade9e8ac2b217a3b6b70',
    '5b17adeae8ac2b25aa06ef85',
    '5b17adece8ac2b24771dcd49',
    '5b17aded4eacab12a43fff94',
    '5b17adee4eacab101902edb7',
    '5b17adf011be100868f9a324',
    '5b17adf111be107ea127e5f5',
    '5b17adf211be100868f9a329',
    '5b17adf3e8ac2b1bdf53c592',
    '5b17adf411be107b322cbdc6',
    '5b17adf54eacab101902edba',
    '5b17adf6e8ac2b21c31ff289',
    '5b518524e8ac2b2948918a8f',
    '5b2260f811be10651e422c14',
    '5b4c656011be106401eedcad',
    '5b4c645511be106c3a4ef8fd',
    '5b518524e8ac2b2948918a8f'


]
