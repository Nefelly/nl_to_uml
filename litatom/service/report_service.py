# coding: utf-8
import time
from ..redis import RedisClient
from ..model import Report
from ..const import ONE_DAY
from ..service import (
    UserService,
)
redis_client = RedisClient()['lit']

class ReportService(object):

    @classmethod
    def report(cls, user_id, reason, pics=[], target_user_id=None, related_feed_id=None):
        report = Report()
        report.uid = user_id
        report.reason =reason
        report.pics = pics
        report.related_feed = related_feed_id
        if target_user_id:
            if target_user_id.startswith('love'):
                target_user_id = UserService.uid_by_huanxin_id(target_user_id)
            report.target_uid = target_user_id
            if cls._should_block(target_user_id, user_id):
                UserService.auto_forbid(target_user_id, 3 * ONE_DAY)
                objs = Report.objects(target_uid=target_user_id, create_ts__gte=(ts_now - 3 * ONE_DAY))
                send_uids = []
                for _ in objs:
                    if not _.dealed:
                        _.dealed = True
                        send_uids.append(_.uid)
                UserService.block_actions(target_user_id, list(set(send_uids)))
        ts_now = int(time.time())
        report.create_ts = ts_now
        report.save()
        return {'report_id': str(report.id)}, True

    @classmethod
    def _should_block(cls, target_user_id, user_id):
        ts_now = int(time.time())
        objs = Report.objects(target_uid=target_user_id, create_ts__gte=(ts_now - 3 * ONE_DAY))
        if objs:
            for _ in objs:
                if _.uid != user_id:
                    return True
        return False

    @classmethod
    def info_by_id(cls, report_id):
        report = Report.get_by_id(report_id)
        if not report:
            return u'worng id', False
        return report.to_json(), True