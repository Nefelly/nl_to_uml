import logging

from hendrix.conf import setting
from .util import BaseDBManager

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


class DBManager(BaseDBManager):
    @property
    def settings(self):
        return setting.DB_SETTINGS

    def _initdb(self, name):
        opts = self.settings[name].copy()
        self[name] = mongoengine.connect(**opts)


# class CommandLogger(monitoring.CommandListener):
#     start = {}
#
#     def _send_metric(self, evt, ok):
#         ns = ''
#         if ok and 'cursor' in evt.reply:
#             ns = evt.reply['cursor']['ns']
#         metrics['mongo.ops'].\
#             tags(ns=ns, op=evt.command_name, ok=ok,
#                  hostname=metrics.HOSTNAME).\
#             values(rid=flask.request.id if flask.request else '',
#                    req_id=evt.request_id,
#                    op_id=evt.operation_id).\
#             commit(evt.duration_micros / 1000)
#
#     def started(self, evt):
#         pass
#
#     def succeeded(self, evt):
#         self._send_metric(evt, True)
#
#     def failed(self, evt):
#         self._send_metric(evt, False)
#         logger.error("%r failed on %s: %r %r %dus",
#                      evt.command_name,
#                      evt.connection_id,
#                      evt.failure,
#                      evt.request_id,
#                      evt.duration_micros,
#                      )

#monitoring.register(CommandLogger())
