import logging

from hendrix.conf import setting
from .metrics import metrics

import flask
import mongoengine
from pymongo import monitoring
from pymongo.errors import AutoReconnect

logger = logging.getLogger(__name__)


def retry(func, times=3, *args, **kwargs):
    for i in range(times):
        try:
            return func(*args, **kwargs)
        except AutoReconnect as e:
            if i >= times - 1:
                raise
            logger.warning('retry db operation on exc: %r', e)

