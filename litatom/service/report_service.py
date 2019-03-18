# coding: utf-8
import time
from ..redis import RedisClient
from ..model import Report
redis_client = RedisClient()['lit']

class ReportService(object):

    @classmethod
    def report(cls, user_id, reason, pics=[], target_user_id=None):
        report = Report()
        report.uid = user_id
        report.reason =reason
        report.pics = pics
        if target_user_id:
            report.target_uid = target_user_id
        report.create_ts = int(time.time())
        report.save()
        return {'report_id': str(report.id)}, True

    @classmethod
    def info_by_id(cls, report_id):
        report = Report.get_by_id(report_id)
        if not report:
            return u'worng id', False
        return report.to_json(), True