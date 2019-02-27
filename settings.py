# coding: utf-8
from hendrix.const import ENV_PROD, INTEGRATION_MODE_COMPONENT
from hendrix.util import EnvvarReader

_envvars = [
    'HENDRIX_ENV',
    'SENTRY_DSN',
    'LL',
    'REDIS_SNS_TAG_LIKE',
    'ELASTICSEARCH_SNS_POI',
    'HENDRIX_IDL_MODULE',
    'HENDRIX_THRIFT_HOST',
    'HENDRIX_THRIFT_PORT'
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


DB_SETTINGS = {
    'db_prod': _get_db_setting('LL', 'LL'),
}
METRICS_SCHEMAS = {'litatom':{'a': {'a':'a'}}}
DEFAULT_REDIS_SETTING = {
    'password': '',
    'host': '127.0.0.1',
    'port': 6379,
    'db': 0,
}
REDIS_SETTINGS = {
    'sns_tag_like': r.get_json('REDIS_SNS_TAG_LIKE', DEFAULT_REDIS_SETTING),

}

ELASTICSEARCH_SETTINGS = {
    'sns_poi': r.get_json('ELASTICSEARCH_SNS_POI', [{
        'host': 'localhost',
    }]),
}
