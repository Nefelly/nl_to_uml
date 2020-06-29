# coding: utf-8

import logging

from raven import Client as SentryClient
from raven.transport.gevent import GeventedHTTPTransport
from hendrix.conf import setting
from hendrix.env import is_prod_env
from hendrix.util import get_hostname

from .log import format_request_data_json
from .util import on_staging, memoize


@memoize
def _get_env():
    if is_prod_env():
        if not on_staging():
            return 'prod'
        else:
            return 'staging'
    return get_hostname()


logger = logging.getLogger(__name__)
# sentry_client = SentryClient(dsn=setting.SENTRY_DSN,
#                              transport=GeventedHTTPTransport,
#                              auto_log_stacks=True,
#                              enable_breadcrumbs=False,
#                              environment=_get_env())


def sentry_exception_handler(request, exc_info):
    if setting.SENTRY_ENABLED:
        try:
            sentry_client.context.merge(_prepare_sentry_context(request))
            sentry_client.captureException(exc_info=exc_info)
        except Exception:
            logger.warning('error sending sentry report')
        finally:
            sentry_client.context.clear()


def _prepare_sentry_context(req):
    """
    extract info from request for sentry report
    :param req: LitatomRequest instance
    :return:
    """
    return {
        'tags': {
            'method': req.method,
            'endpoint': req.endpoint,
            'platform': req.platform,
            'build': req.build,
            'version': req.version,
        },
        'user': {
            'id': req.user_id,
            'ip_address': req.ip,
        },
        'extra': {
            'request_id': req.id,
            'full_path': req.full_path,
            'request_data': format_request_data_json(req),
            'device': req.manufactor_and_device,
            'device_id': req.device_id,
        }
    }
