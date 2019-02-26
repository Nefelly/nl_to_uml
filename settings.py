# coding: utf-8
from hendrix.const import ENV_PROD, INTEGRATION_MODE_COMPONENT
from hendrix.util import EnvvarReader

_envvars = [
    'HENDRIX_ENV',
    'SENTRY_DSN',
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
    'db_prod': _get_db_setting('ll', '11'),
}

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

CB_ENABLED = r.get_bool('CB_ENABLED', True)
CB_WINDOW = r.get_int('CB_WINDOW', 20 * 1000)
CB_INTERVAL = r.get_int('CB_INTERVAL', 1000)
CB_MAX_FAIL = r.get_int('CB_MAX_FAIL', 3)

