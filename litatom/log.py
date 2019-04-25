# coding: utf-8
import itertools
import json
import logging
from contextlib import contextmanager
import re
import sys

from flask import request
from hendrix.const import ENV_DEV
from hendrix.env import get_current_env
from hendrix.util import get_hostname

from .const import LOGGING_PRDLINE, LOGGING_APP_NAME
from .util import (
    in_container,
    on_staging,
)

FORMAT_SYSLOG = '%(name)s[%(process)d] %(message)s'
FORMAT_STDOUT = '%(message)s'
FORMAT_CONSOLE = '>>> %(asctime)s %(levelname)-7s ' + FORMAT_STDOUT


@contextmanager
def record_context(record, **attr):
    # Backup before changing the content of record,
    # or next handlers will choke on your dirty data
    _backup_dict = {}
    for key, value in attr.iteritems():
        _backup_dict[key] = value
    try:
        yield record
    finally:
        for key, value in _backup_dict.iteritems():
            setattr(record, key, value)


class LitatomFormatter(logging.Formatter):
    MSG_SEPARATOR = '@@'

    def _format_meta(self):
        meta = []

        def _add_meta(pat, vals):
            meta.append((pat, vals))

        if request:
            def _get_user_id():
                if request.has_user_session:
                    return request.user_id

            _add_meta('rid:%s', _get_log_value(lambda: request.id))
            _add_meta('ep:%s', _get_log_value(lambda: request.endpoint))
            _add_meta('ip:%s', _get_log_value(lambda: ','.join(request.ip_full_list)))
            _add_meta('user_id:%s', _get_log_value(lambda: _get_user_id()))
            _add_meta('device_id:%s', _get_log_value(lambda: request.device_id))
            _add_meta('os:%s', _get_log_value(lambda: request.platform))

        meta_msg = ''
        if meta:
            meta_msg = ' '.join([m[0] % m[-1] for m in meta])
        return meta_msg

    def _format_msg(self, msg):
        meta_msg = self._format_meta()
        if meta_msg:
            return meta_msg + ' ' + msg
        return msg

    def _format(self, record):
        msg = self.MSG_SEPARATOR + ' ' + record.msg
        record.msg = self._format_msg(msg)
        try:
            return super(LitatomFormatter, self).format(record)
        except UnicodeError:
            if isinstance(record.msg, unicode):
                record.msg = record.msg.encode('utf-8')
            if record.args:
                args = []
                for a in record.args:
                    if isinstance(a, unicode):
                        a = a.encode('utf-8')
                    args.append(a)
                record.args = tuple(args)
            return super(LitatomFormatter, self).format(record)

    def format(self, record):
        with record_context(record, msg=record.msg):
            return self._format(record)


class LitatomPrefixedFormatter(LitatomFormatter):
    def __init__(self, prefix, *args, **kwargs):
        self.prefix = prefix
        super(LitatomPrefixedFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        with record_context(record, name=record.name):
            record.name = self.prefix + '.' + record.name
            return super(LitatomPrefixedFormatter, self).format(record)


def sanitize_sensitive_data(value):
    """
    将字符串中的敏感信息过滤掉
    参考 https://github.com/getsentry/sentry/blob/master/src/sentry/utils/data_scrubber.py
    """
    # various private/public keys
    KEY_PAIR_RE = re.compile(r'-----BEGIN[A-Z ]+(PRIVATE|PUBLIC) KEY-----.+-----END[A-Z ]+(PRIVATE|PUBLIC) KEY-----')
    # url-like object containing a password
    # e.g. postgres://foo:password@example.com/db
    URL_PASSWORD_RE = re.compile(r'\b((?:[a-z0-9]+:)?//[a-zA-Z0-9%_.-]+:)([a-zA-Z0-9%_.-]+)@')
    FILTER_MASK = '******'

    if KEY_PAIR_RE.match(value):
        return FILTER_MASK

    if '//' in value and '@' in value:
        value = URL_PASSWORD_RE.sub(r'\1' + FILTER_MASK + '@', value)

    return value


class LogItemFilter(object):
    def filter_invalid_key_name(self, k):
        if re.search(r'[^a-zA-Z0-9_]', k):
            return k, True
        return k, False

    def filter_invalid_chars(self, k):
        tr_map = {
            '\t': '#011',
            '\n': '#012',
            ' ': '#040',
            '.': '#056',
        }
        filtered = False
        for f, t in tr_map.iteritems():
            if f in k:
                k = k.replace(f, t)
                filtered = True
        return k, filtered

    key_filters = [
        filter_invalid_key_name,
        filter_invalid_chars,
    ]

    def filter_key(self, k):
        filtered = False
        for kf in self.key_filters:
            k, fed = kf(self, k)
            if fed:
                filtered = True
        return k, filtered


def _format_value_str(v):
    try:
        v_str = '%s' % v
    except Exception:
        v_str = '-'
    return v_str


INVALID_DATA_KEY = 'invalid_data'


def _fill_log_data_mapping(d, k, v):
    """
    Args:
      d: the data mapping dict
      k: log field key
      v: log field value
    """
    if k in ('password', 'pass', 'passwd'):
        v = '***'
    v = sanitize_sensitive_data(_format_value_str(v))
    log_item_filter = LogItemFilter()
    k, filtered = log_item_filter.filter_key(k)
    if filtered:
        if INVALID_DATA_KEY not in d:
            d[INVALID_DATA_KEY] = []
        d[INVALID_DATA_KEY].append('{!r}:{!r}'.format(k, v))
    else:
        d[k] = v


def format_request_data_json(request):
    """
    extract data from request form/json/files
    """
    d = {}
    if request.form:
        req_data = request.form
    else:
        try:
            req_data = request.get_json() or {}
        except Exception:
            req_data = {}
    for k, v in itertools.chain(req_data.iteritems(),
                                request.files.iteritems()):
        _fill_log_data_mapping(d, k, v)
    return d


def format_query_params_json(request):
    """
    extract data from request URL query parameters
    """
    d = {}
    if request.args:
        for k, v in request.args.iteritems():
            _fill_log_data_mapping(d, k, v)
    return d


class LitatomJsonFormatter(logging.Formatter):
    """
    output log as json

    current json fields are:
    {
        'logger': 'litatom', # logger name
        'level': 'ERROR', # log level
        'message': 'I do not expect this', # log message
        'asctime': '2017-05-26 13:02:57,498', # timestamp
        'exc_text': 'Traceback...', # exception info
        'request_id': '95acfa65db9e4e94ab2488303b176217', # request id
        'method': 'POST', # http method name
        'endpoint': 'api_v1.note-comment', # endpoint name
        'full_path': '/api/sns/v2/note/comment?sid=ssvf3456', # request url with query string
        'query_params': {
                'sid': 'session.1172953060171812760',
                'sign': '207f304412f41bf2af02e121e0dfe2a2'
            }, # URL query parameters
        'request_data': {
                'username': 'shk',
                'passwd': '***',
            }, # request data
        'time_cost': 78, # request processing time, in milliseconds
        'hostname': 'sns-litatom-staging', # hostname
        'ip_route': ['186.23.67.123', '10.34.23.15'], # ip route path
        'ip_client': '186.23.67.123', # real ip of client (first element of route path)
        'user_id': '581b131182ec39020338c06a', # user id
        'platform': 'android', # mobile platform name
        'build': 421015, # app build version code
        'version': '4.21', # app version name
        'device': ['xiaomi', '6'], # device manufactor and name
        'device_id': '2f28bc9f-76ce-33c0-8b66-fc739a6c6a6b', # device id
        'status_code': 503, # http response status code
        'resp_result': -9901, # api response error code
        'resp_msg': 'shuduizhang is crying', # api response message
        'form_errors': 'username must exists', # http request form errors
    }
    """

    def _prepare_meta(self):
        """
        prepare meta info as dict, for ultimate json log
        """
        meta = {}

        if request:
            meta.update({
                'env': get_current_env(),
                'request_id': request.id,
                'method': request.method,
                'endpoint': request.endpoint,
                'full_path': sanitize_sensitive_data(request.full_path),
                'query_params': format_query_params_json(request),
                'request_data': format_request_data_json(request),
                'time_cost_relative': _get_log_value(lambda: request.ctx.api_cost, default=None),
                'hostname': get_hostname(),
                'ip_route': request.ip_full_list,
                'ip_client': request.ip,
                'user_id': request.user_id if request.has_user_session else '',
                'platform': request.platform,
                'build': request.build,
                'version': request.version,
                'device': request.manufactor_and_device,
                'device_id': request.device_id,
            })
            if request.ctx is not None and request.ctx._api_finished:
                meta.update({
                    'time_cost': _get_log_value(lambda: request.ctx.api_cost, default=None),
                })

        return meta

    def _get_logging_origin(self, record):
        pattern = '{0.pathname}+{0.lineno}:{0.funcName}'
        return pattern.format(record)

    def _build_log_data(self, record):
        # Combine record.msg and record.args to yield the 'message' field of our json
        try:
            raw_msg = record.getMessage()
        except UnicodeError:
            if isinstance(record.msg, str):
                record.msg = record.msg.decode('utf-8', 'replace')
            if record.args:
                args = []
                for a in record.args:
                    if isinstance(a, str):
                        a = a.decode('utf-8', 'replace')
                    args.append(a)
                record.args = tuple(args)
            raw_msg = record.getMessage()

        d = {
            'logger': record.name,
            'level': record.levelname,
            'levelno': record.levelno,
            'message': raw_msg,
            'asctime': self.formatTime(record, self.datefmt),
            'process_name': record.processName,
            'process_id': record.process,
            'thread_name': record.threadName,
            'thread_id': record.thread,
            'origin': self._get_logging_origin(record),
            'module': record.module,
            'timestamp': record.created,
        }

        if in_container():
            d.update({
                'prdline': LOGGING_PRDLINE,
                'app': LOGGING_APP_NAME,
            })

        # exception info
        if record.exc_text:
            d['exc_text'] = record.exc_text
        elif record.exc_info:
            d['exc_text'] = self.formatException(record.exc_info)

        # data passed by logging.xxx(extra={})
        for ex_key in ('status_code', 'resp_result', 'resp_msg', 'form_errors'):
            if hasattr(record, ex_key):
                d[ex_key] = getattr(record, ex_key)

        # other meta data
        d.update(self._prepare_meta())
        return d

    def _format_msg(self, record):
        log_data = self._build_log_data(record)
        return json.dumps(log_data)

    def _format(self, record):
        record.msg = self._format_msg(record)
        # prevent record.msg from being formatted by record.args
        record.args = ()
        # change record.name for rsyslog to redirect
        record.name = 'json.' + record.name
        # prevent exc_text from being appended
        record.exc_info = None
        record.exc_text = ''

        try:
            return super(LitatomJsonFormatter, self).format(record)
        except Exception:
            return ''

    def format(self, record):
        with record_context(
                record, msg=record.msg, args=record.args, name=record.name,
                exc_info=record.exc_info, exc_text=record.exc_text):
            return self._format(record)


class LitatomJsonPrettyFormatterMixin(object):
    def _format_msg(self, record):
        log_data = self._build_log_data(record)
        return json.dumps(log_data, indent=2, separators=(', ', ': '), sort_keys=True)


class LitatomJsonPrettyFormatter(LitatomJsonPrettyFormatterMixin, LitatomJsonFormatter):
    pass


class LitatomJsonPrefixedFormatter(LitatomJsonFormatter):
    def __init__(self, prefix, *args, **kwargs):
        self.prefix = prefix
        super(LitatomJsonPrefixedFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        with record_context(record, name=record.name):
            record.name = self.prefix + '.' + record.name
            return super(LitatomJsonPrefixedFormatter, self).format(record)


class LitatomJsonPrettyPrefixedFormatter(LitatomJsonPrettyFormatterMixin, LitatomJsonPrefixedFormatter):
    pass


def _get_logging_handler(need_prefix=False):
    """
    所有机器都使用结构化的LitatomJsonFormatter
    如果是staging机器，还需要保留更容易阅读的LitatomFormatter
    """
    handlers = set()
    if in_container():
        handlers.update(['stdout_json'])
    else:
        handlers.update(['syslog_json'])
        if on_staging():
            handlers.update(['syslog', 'stdout_json_pretty'])

    handlers = list(handlers)
    if need_prefix:
        for i, _ in enumerate(handlers):
            handlers[i] += '_prefixed'
    return handlers


def _gen_online_handlers():
    handlers = {
        # stdout
        'stdout_json': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'stdout_json',
        },
        'stdout_json_pretty': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'stdout_json_pretty',
        },
        'stdout_json_prefixed': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'stdout_json_prefixed',
        },
        'stdout_json_pretty_prefixed': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'stdout_json_pretty_prefixed',
        },
    }
    if not in_container():
        handlers.update({
            # syslog
            'syslog': {
                'level': 'INFO',
                'class': 'logging.handlers.SysLogHandler',
                'address': '/rdata/litlog',
                'facility': 'local6',
                'formatter': 'syslog',
            },
            'syslog_prefixed': {
                'level': 'INFO',
                'class': 'logging.handlers.SysLogHandler',
                'address': '/dev/log',
                'facility': 'local6',
                'formatter': 'syslog_prefixed',
            },
            'syslog_json': {
                'level': 'INFO',
                'class': 'logging.handlers.SysLogHandler',
                'address': '/dev/log',
                'facility': 'local6',
                'formatter': 'syslog_json',
            },
            'syslog_json_prefixed': {
                'level': 'INFO',
                'class': 'logging.handlers.SysLogHandler',
                'address': '/dev/log',
                'facility': 'local6',
                'formatter': 'syslog_json_prefixed',
            },
        })
    return handlers


def _gen_online_config(app_name):
    return {
        'version': 1,
        'root': {
            'handlers': _get_logging_handler(need_prefix=True),
            'level': 'INFO',
        },
        'loggers': {
            app_name: {
                'handlers': _get_logging_handler(),
                'propagate': False,
                'level': 'INFO',
            },
            'celery': {
                'handlers': _get_logging_handler(need_prefix=True),
                'propagate': False,
                'level': 'INFO',
            },
            'hendrix': {
                'handlers': _get_logging_handler(need_prefix=True),
                'propagate': False,
                'level': 'INFO',
            },
            'elasticsearch': {
                'handlers': _get_logging_handler(need_prefix=True),
                'propagate': False,
                'level': 'INFO',
            },
            'pika.adapters.base_connection': {
                'handler': [],
                'propagate': False,
                'level': 'INFO',
            }
        },
        'handlers': _gen_online_handlers(),
        'formatters': {
            # syslog
            'syslog': {
                '()': LitatomFormatter,
                'format': FORMAT_SYSLOG,
            },
            'syslog_prefixed': {
                '()': LitatomPrefixedFormatter,
                'format': FORMAT_SYSLOG,
                'prefix': app_name,
            },
            'syslog_json': {
                '()': LitatomJsonFormatter,
                'format': FORMAT_SYSLOG,
            },
            'syslog_json_prefixed': {
                '()': LitatomJsonPrefixedFormatter,
                'format': FORMAT_SYSLOG,
                'prefix': app_name,
            },

            # stdout
            'stdout_json': {
                '()': LitatomJsonFormatter,
                'format': FORMAT_STDOUT,
            },
            'stdout_json_pretty': {
                '()': LitatomJsonPrettyFormatter,
                'format': FORMAT_STDOUT,
            },
            'stdout_json_prefixed': {
                '()': LitatomJsonPrefixedFormatter,
                'format': FORMAT_STDOUT,
                'prefix': app_name,
            },
            'stdout_json_pretty_prefixed': {
                '()': LitatomJsonPrettyPrefixedFormatter,
                'format': FORMAT_STDOUT,
                'prefix': app_name,
            },
        },
    }


def _gen_console_config(app_name):
    return {
        'version': 1,
        'root': {
            'handlers': ['console_prefixed'],
            'level': 'INFO',
        },
        'loggers': {
            app_name: {
                'handlers': ['console'],
                'propagate': False,
                'level': 'DEBUG',
            },
            'celery': {
                'handlers': ['console_prefixed'],
                'propagate': False,
                'level': 'DEBUG',
            },
            'hendrix': {
                'handlers': ['console_prefixed'],
                'propagate': False,
                'level': 'DEBUG',
            },
            'elasticsearch': {
                'handlers': ['console_prefixed'],
                'propagate': False,
                'level': 'DEBUG',
            },
            'elasticsearch.trace': {
                'handlers': ['console_prefixed'],
                'propagate': False,
                'level': 'DEBUG',
            },
        },
        'handlers': {
            'console': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'console',
            },
            'console_prefixed': {
                'level': 'DEBUG',
                'class': 'logging.StreamHandler',
                'formatter': 'console_prefixed',
            },
        },
        'formatters': {
            'console': {
                '()': LitatomJsonPrettyFormatter,
                'format': FORMAT_CONSOLE,
            },
            'console_prefixed': {
                '()': LitatomJsonPrettyPrefixedFormatter,
                'format': FORMAT_CONSOLE,
                'prefix': app_name,
            },
        }
    }


def gen_app_log_config(name, debug=False):
    print 'current env', get_current_env()
    if get_current_env() != ENV_DEV:
        return _gen_online_config(name)
    else:
        conf = _gen_console_config(name)
        if debug:
            conf['loggers']['werkzeug'] = {
                'handlers': ['console_prefixed'],
                'propagate': False,
                'level': 'INFO',
            }
        return conf


def _format_request_data():
    def _format_value_str(v):
        try:
            v_str = '%s' % v
        except Exception:
            v_str = '-'
        return v_str

    d = {}
    if request.form:
        d = request.form
    else:
        try:
            d = request.get_json() or {}
        except Exception:
            pass
    data = []
    for k, v in d.iteritems():
        if k in ['password', 'pass', 'passwd']:
            v = '***'
        value = '%s=%s' % (k, _format_value_str(v))
        data.append(value)
    file = []
    for k, v in request.files.iteritems():
        value = '%s=%s' % (k, _format_value_str(v))
        file.append(value)
    data_str = ''
    if data:
        data_str += '[%s]' % ' '.join(data)
    if file:
        data_str += '[%s]' % ' '.join(file)
    return data_str


def log_api_failure(logger, response=None):
    log_data = []
    extra = {}
    if response and not response.success and response.json:
        result = _get_log_value(lambda: response.json.get('result') or response.json.get('error_code'))
        log_data.append(('%s', result))
        extra['resp_result'] = result

        if 'msg' in response.json:
            msg = _get_log_value(lambda: response.json['msg'])
            log_data.append(('%s', msg))
            extra['resp_msg'] = msg

    if request.form_errors:
        form_errors = _get_log_value(lambda: request.form_errors or '-')
        log_data.append(('%s', form_errors))
        extra['form_errors'] = form_errors

    if log_data:
        logger.info('api failed: ' + ' '.join([x[0] for x in log_data]),
                    *[x[1] for x in log_data], extra=extra)


def _get_log_value(func, fallback='-', default='-'):
    """
    :param callable func: log value getter
    :param fallback: if exception happens when calling ``func``, this
                     value will be used instead
    :param default: if ``func`` returns a falsy value and this is not None,
                    it will be used instead
    """
    try:
        value = func()
    except Exception:
        # do not log, preventing endless loop
        value = fallback
    else:
        if not value and default is not None:
            value = default
    return value


def log_api_call(logger, exc=None, status_code=None):
    log_data = [
        ('%s', _get_log_value(lambda: request.method)),
        ('%s', _get_log_value(lambda: request.full_path)),
        # ('%s', _get_log_value(_format_request_data)),  # reduce msg size due to rsyslog limit
        ('%s', _get_log_value(lambda: request.user_agent.string)),
        ('%s', _get_log_value(lambda: status_code)),
        ('%dms', _get_log_value(lambda: request.ctx.api_cost, default=None)),
    ]

    extra = {
        'status_code': status_code
    }

    if exc is not None:
        log = logger.exception
    elif status_code >= 400:
        log = logger.error
    else:
        log = logger.info
    log(' '.join([x[0] for x in log_data]), *[x[1] for x in log_data], extra=extra)
