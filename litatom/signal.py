# coding: utf-8
import logging
import sys

from flask import g, request
from hendrix.conf import setting

from . import context
from .log import (
    log_api_call,
    log_api_failure,
)
from .metrics import metrics
from .sentry import sentry_exception_handler

logger = logging.getLogger(__name__)
if setting['CB_ENABLED']:
    from .circuit_breaker import CircuitBreaker
    cb = CircuitBreaker(window=setting['CB_WINDOW'],
                        interval=setting['CB_INTERVAL'],
                        max_fail=setting['CB_MAX_FAIL'],
                        open_time=setting['CB_OPEN_TIME'],
                        half_open_time_ratio=setting['CB_HALF_OPEN_TIME_RATIO'])
else:
    cb = None


def before_first_request_handler():
    ctx = request.ctx = context.get_ctx()
    ctx.api_start()
    # from .bgtask.tasks import celery
    # logger.info('celery tasks imported: %r', celery.tasks.keys())


def request_started_handler(sender, **extra):
    try:
        ctx = request.ctx = context.get_ctx()
        ctx.api_start()
    except Exception:
        logger.exception('error handling signal: `request_started`')


def _process_circuit_breaker():
    if not setting['CB_ENABLED']:
        return

    ep = request.endpoint
    g.is_circuit_broken = False
    if cb.can_passthrough(ep):
        return

    g.is_circuit_broken = True
    metrics['api.circuit_breaker'].\
        tags(endpoint=ep, hostname=metrics.HOSTNAME).\
        values(rid=request.id).\
        commit(1)
    return '', 503


def before_request_handler():
    try:
        return _process_circuit_breaker()
    except Exception:
        logger.exception('error preprocessing request')


def _send_api_metrics(exc=None, response=None):
    if not (exc or response):
        logger.error('missing either `exc` or `response`, metrics not sent')
    tags = {
        'endpoint': request.endpoint,
        'exc': bool(exc),
        'success': bool(not exc and response.success),
        'platform': request.platform,
        'hostname': metrics.HOSTNAME,
    }
    metrics['api_calls'].\
        tags(**tags).\
        values(rid=request.id).\
        commit(request.ctx.api_cost)


def got_request_exception_handler(sender, **extra):
    try:
        exc_info = sys.exc_info()
        ctx = context.get_ctx()
        ctx.api_finish()
        exc = extra['exception']
        if setting['CB_ENABLED'] and \
                not g.is_circuit_broken:
            cb.inc_error(request.endpoint)
        _send_api_metrics(exc=exc)
        log_api_failure(sender.logger)
        sentry_exception_handler(request, exc_info)
    except Exception:
        logger.exception('error handling signal: `got_request_exception`')
    finally:
        del exc_info


def request_finished_handler(sender, response, **extra):
    try:
        ctx = context.get_ctx()
        ctx.api_finish()
        _send_api_metrics(response=response)
        if not response.success:
            log_api_failure(sender.logger, response=response)
        log_api_call(sender.logger, status_code=response.status_code)
    except Exception:
        logger.exception('error handling signal: `request_finished`')


def teardown_request_handler(exc):
    try:
        if setting['CB_ENABLED'] and \
                cb.is_half_open(request.endpoint) and \
                not g.is_circuit_broken:
            cb.inc_success(request.endpoint)
    except Exception:
        logger.exception('error tearing down request')
    finally:
        context.clear_ctx()
