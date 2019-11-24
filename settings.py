# coding: utf-8
from hendrix.const import ENV_PROD, INTEGRATION_MODE_COMPONENT
from hendrix.util import EnvvarReader

_envvars = [
    'HENDRIX_ENV',
    'SENTRY_DSN',
    'DB_LIT',
    'DB_DEV_LIT',
    'DB_ALI_LIT',
    'DB_HUANXIN_MESSAGE',
    'REDIS_SNS_TAG_LIKE',
    'ELASTICSEARCH_SNS_POI',
    'HENDRIX_IDL_MODULE',
    'HENDRIX_THRIFT_HOST',
    'HENDRIX_THRIFT_PORT',
    'REDIS_LIT',
    'REDIS_ALI_LIT',
    'HUANXIN_ACCOUNT',
    'IS_DEV',
    'DEFAULT_MQ_PRODUCER',
    'DEFAULT_MQ_PRODUCER_PASSWORD',
    'DEFAULT_MQ_HOST',
    'DEFAULT_MQ_PORT',
    'DEFAULT_MQ_VHOST'
]

r = EnvvarReader(*_envvars)

ENV = HENDRIX_ENV = r.get('HENDRIX_ENV', ENV_PROD)

SENTRY_DSN = r.get('SENTRY_DSN', '')

def _get_db_setting(envvar, db, alias=None):
    local_db_url = 'mongodb://localhost:27017'
    default = {
        'host': '/'.join([local_db_url, db]),
    }
    if alias:
        default.update({'alias': alias})
    url = r.get_json(envvar, default)
    return url

CB_ENABLED = False

METRICS_SCHEMAS = {'litatom':{'a': {'a': 'a'}}}   # no use

DB_SETTINGS = {
    'DB_LIT': _get_db_setting('DB_LIT', 'lit', 'lit'),
    'dev_lit': _get_db_setting('DB_DEV_LIT', 'lit', 'dev_lit'),  # envar, db, alias,
    'huanxin_message': _get_db_setting('DB_HUANXIN_MESSAGE', 'huanxin_message', 'huanxin_message')
}


DEFAULT_REDIS_SETTING = {
    'password': '',
    'host': '127.0.0.1',
    'port': 6379,
    'db': 0,
}


REDIS_SETTINGS = {
    'lit_ali': r.get_json('REDIS_LIT', DEFAULT_REDIS_SETTING),
    'lit': r.get_json('REDIS_ALI_LIT', DEFAULT_REDIS_SETTING),

}
IS_DEV = r.get_bool('IS_DEV', False)
DEFAULT_MQ_PRODUCER = r.get('DEFAULT_MQ_PRODUCER', 'litatom')
DEFAULT_MQ_PRODUCER_PASSWORD = r.get('DEFAULT_MQ_PRODUCER_PASSWORD',  'julele673215')
DEFAULT_MQ_HOST = r.get('DEFAULT_MQ_HOST',  '47.244.141.151')
DEFAULT_MQ_PORT = r.get('DEFAULT_MQ_PORT',  5672)
DEFAULT_MQ_VHOST = r.get('DEFAULT_MQ_VHOST',  'test' if IS_DEV else 'online')

DEFAULT_HUANXIN_SETTING = {
    'org_name': '1102190223222824',
    'app_name': 'lit',
    'client_id': 'YXA6ALfHYDd7EemQqCO501ONvQ',
    'client_secret': 'YXA6AH1kFGkcUc67KcpClt5rWA23zv4'
}

HUANXIN_ACCOUNT = r.get_json('HUANXIN_ACCOUNT', DEFAULT_HUANXIN_SETTING)


ELASTICSEARCH_SETTINGS = {
    'sns_poi': r.get_json('ELASTICSEARCH_SNS_POI', [{
        'host': 'localhost',
    }]),
}
